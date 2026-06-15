// Browser e2e for the Antigreedy A/B Theater (drives the real dashboard stack).
// Test cases derived from the v0.2 plan (PRD §12): E1 comprehension UX,
// E2 in-dashboard policy editor (the live "wow"), E3 experiment history.
import { test, expect } from '@playwright/test';

const DENY_A = `from antigreedy.governance.policy import Policy


class DenyA(Policy):
    name = "deny_a"
    priority = 1

    def evaluate(self, action, state, history):
        if action.agent_id == "A":
            return self.deny(reason="A muted by e2e policy")
        return self.allow()
`;

// Click ▶ Run A/B and wait until the run finishes (button re-enabled).
async function runAB(page) {
  await page.locator('#run').click();
  await expect(page.locator('#feed-governed div').first()).toBeVisible();
  await expect(page.locator('#run')).toBeEnabled({ timeout: 30_000 });
}

test.describe('E1 — beginner-friendly comprehension UX', () => {
  test('glossary, legend, empty-state and per-button help are visible', async ({ page }) => {
    await page.goto('/');

    // jargon glosses (commons / airtime / verdict)
    await expect(page.getByText('the shared token budget', { exact: false })).toBeVisible();
    await expect(page.locator('.gloss')).toContainText('Airtime');
    await expect(page.locator('.gloss')).toContainText('Verdict');

    // legend maps the visuals
    const legend = page.locator('.legend');
    await expect(legend).toContainText('Legend');
    await expect(legend).toContainText('allow');
    await expect(legend).toContainText('modify');
    await expect(legend).toContainText('deny');
    await expect(legend).toContainText('airtime');

    // empty-state guidance before any run
    await expect(page.locator('#g-baseline .empty')).toContainText('Run A/B');
    await expect(page.locator('#g-governed .empty')).toBeVisible();

    // per-button "what this does" help
    await expect(page.locator('.controls')).toContainText('What this does');
    await expect(page.locator('.controls')).toContainText('side-by-side');
  });
});

test.describe('E2 — in-dashboard policy editor (the live wow)', () => {
  test('localhost warning + seeded policy list are shown', async ({ page }) => {
    await page.goto('/');
    await page.locator('#editor > summary').click();          // expand the editor
    await expect(page.locator('#ed-warn')).toContainText('Localhost only');
    // seeded repo policies appear in the active list
    await expect(page.locator('#pol-list')).toContainText('10_airtime_quota.py');
  });

  test('a syntax-error policy is rejected with an error status', async ({ page }) => {
    await page.goto('/');
    await page.locator('#editor > summary').click();
    await page.locator('#pol-name').fill('90_broken.py');
    await page.locator('#pol-source').fill('def (');           // invalid Python
    await page.locator('#pol-save').click();
    await expect(page.locator('#pol-status')).toHaveClass(/err/);
    await expect(page.locator('#pol-status')).toContainText('syntax');
  });

  test('paste a policy → save → it governs the next A/B run (agent A denied)', async ({ page }) => {
    await page.goto('/');
    await page.locator('#editor > summary').click();
    await page.locator('#pol-name').fill('99_deny_a.py');
    await page.locator('#pol-source').fill(DENY_A);
    await page.locator('#pol-save').click();

    // saved → status ok + appears in the active policy list
    await expect(page.locator('#pol-status')).toHaveClass(/ok/);
    await expect(page.locator('#pol-list')).toContainText('99_deny_a.py');

    // the pasted policy now governs the governed side: A's turns show "deny"
    await runAB(page);
    const govFeed = page.locator('#feed-governed');
    await expect(govFeed.locator('.v-deny').first()).toBeVisible();
    await expect(govFeed).toContainText('A');

    // cleanup so re-runs start clean (shared server state)
    await page.locator('#pol-list .item', { hasText: '99_deny_a.py' }).locator('.del').click();
    await expect(page.locator('#pol-list')).not.toContainText('99_deny_a.py');
  });
});

test.describe('Conversation view — see each prompt + output + delivered', () => {
  test('clicking a governed turn reveals prompt, agent output and delivered text', async ({ page }) => {
    await page.goto('/');
    await runAB(page);
    await page.locator('#feed-governed .turnrow').first().click();
    const detail = page.locator('#feed-governed .turndetail').first();
    await expect(detail).toBeVisible();
    await expect(detail).toContainText('PROMPT');
    await expect(detail).toContainText('AGENT OUTPUT');
    await expect(detail).toContainText('DELIVERED');
  });
});

test.describe('Governance presets — swap the governed set', () => {
  test('selecting a preset applies it and changes governed behavior', async ({ page }) => {
    await page.goto('/');
    // dropdown is populated from /presets
    await expect(page.locator('#preset option')).toHaveCount(3);

    // pick "strict" → applied + the strict policy shows in the active list
    await page.locator('#preset').selectOption('strict');
    await expect(page.locator('#preset-status')).toHaveClass(/ok/);
    await expect(page.locator('#pol-list')).toContainText('strict');

    // strict governance bites on the next run (modify or deny)
    await runAB(page);
    await expect(page.locator('#feed-governed .v-deny, #feed-governed .v-modify').first())
      .toBeVisible();

    // restore the default so the shared server is left clean
    await page.locator('#preset').selectOption('quota');
    await expect(page.locator('#preset-status')).toHaveClass(/ok/);
  });
});

test.describe('E3 — experiment history (persist + replay)', () => {
  test('a finished run appears in History and can be re-opened to replay', async ({ page }) => {
    await page.goto('/');
    await runAB(page);                                          // produces a run

    // open History and refresh
    await page.locator('#history > summary').click();
    await page.locator('#hist-refresh').click();
    const firstRow = page.locator('#hist-list .item .fn').first();
    await expect(firstRow).toBeVisible();
    await expect(firstRow).toContainText('ab');                 // mode label

    // re-open → replay re-renders the panels
    await firstRow.click();
    await expect(page.locator('#p-governed h2')).toContainText('replay');
    await expect(page.locator('#hist-status')).toContainText('replaying');
    // replayed event log re-rendered nodes into the governed graph
    // (Cytoscape paints several stacked <canvas> layers — assert the first)
    await expect(page.locator('#g-governed canvas').first()).toBeVisible();
  });
});
