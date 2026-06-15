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

    // jargon glosses (commons / airtime / verdict) — Korean copy
    await expect(page.getByText('공유 토큰 예산', { exact: false }).first()).toBeVisible();
    await expect(page.locator('.gloss')).toContainText('발언량');
    await expect(page.locator('.gloss')).toContainText('판정');

    // legend maps the visuals
    const legend = page.locator('.legend');
    await expect(legend).toContainText('범례');
    await expect(legend).toContainText('allow');
    await expect(legend).toContainText('modify');
    await expect(legend).toContainText('deny');
    await expect(legend).toContainText('발언량');

    // empty-state guidance before any run
    await expect(page.locator('#g-baseline .empty')).toContainText('시작');
    await expect(page.locator('#g-governed .empty')).toBeVisible();

    // per-button help text
    await expect(page.locator('.controls')).toContainText('하는 일');
    await expect(page.locator('.explain')).toContainText('나란히');
  });
});

test.describe('E2 — in-dashboard policy editor (the live wow)', () => {
  test('localhost warning + seeded policy list are shown', async ({ page }) => {
    await page.goto('/');
    await page.locator('#editor > summary').click();          // expand the editor
    await expect(page.locator('#ed-warn')).toContainText('localhost');
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
    await expect(detail).toContainText('프롬프트');
    await expect(detail).toContainText('에이전트 출력');
    await expect(detail).toContainText('전달됨');
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
    await expect(page.locator('#p-governed h2')).toContainText('재생');
    await expect(page.locator('#hist-status')).toContainText('재생');
    // replayed event log re-rendered nodes into the governed graph
    // (Cytoscape paints several stacked <canvas> layers — assert the first)
    await expect(page.locator('#g-governed canvas').first()).toBeVisible();
  });
});

test.describe('Fairness metrics — Jain readout after a run', () => {
  test('both panels show a Jain fairness readout when the run ends', async ({ page }) => {
    await page.goto('/');
    await runAB(page);
    await expect(page.locator('#metrics-governed')).toContainText('공정성(Jain)');
    await expect(page.locator('#metrics-baseline')).toContainText('공정성(Jain)');
    await expect(page.locator('#metrics-governed')).toContainText('발언 점유');
  });
});

test.describe('Agent count — configurable number of agents', () => {
  test('selecting 3 agents runs a 3-agent meeting (no agent D)', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('#agents option')).toHaveCount(7);   // 2..8
    await expect(page.locator('#agents')).toHaveValue('4');         // default
    await page.locator('#agents').selectOption('3');
    await runAB(page);
    const gov = page.locator('#feed-governed');
    await expect(gov).toContainText('C');        // agent C spoke
    await expect(gov).not.toContainText('D');    // no 4th agent in a 3-agent run
  });
});
