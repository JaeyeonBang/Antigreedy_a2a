"""다중 시드 측정용 신뢰구간 primitive (N=1 한계 보완).

- wilson_interval: 이항 비율(예: '전원 완료한 에피소드 비율')의 양측 Wilson 구간.
  기존 wilson_lower(하한만)와 하한이 일치해야 한다(일관성).
- mean_ci: 연속값(예: top_share)의 평균 ± 정규근사 신뢰구간.
"""
import math

from antigreedy.metrics import mean_ci, wilson_interval, wilson_lower


def test_wilson_interval_brackets_point_estimate():
    lo, hi = wilson_interval(8, 10)
    assert 0.0 <= lo < 0.8 < hi <= 1.0       # 점추정 0.8을 사이에 둠
    assert lo < hi


def test_wilson_interval_lower_matches_wilson_lower():
    lo, _ = wilson_interval(8, 10)
    assert math.isclose(lo, wilson_lower(8, 10), rel_tol=1e-9)


def test_wilson_interval_zero_n_is_degenerate():
    assert wilson_interval(0, 0) == (0.0, 0.0)


def test_wilson_interval_all_success_upper_is_one_ish():
    lo, hi = wilson_interval(10, 10)
    assert hi >= 0.99 and lo > 0.6           # 10/10 → 상한≈1, 하한은 1보다 꽤 낮음(작은 n)


def test_mean_ci_constant_has_zero_width():
    mean, lo, hi = mean_ci([0.5, 0.5, 0.5, 0.5])
    assert mean == 0.5 and lo == 0.5 and hi == 0.5


def test_mean_ci_is_symmetric_around_mean():
    mean, lo, hi = mean_ci([0.2, 0.4, 0.6, 0.8])
    assert math.isclose(mean, 0.5, abs_tol=1e-9)
    assert math.isclose(mean - lo, hi - mean, rel_tol=1e-9)   # 대칭
    assert lo < mean < hi


def test_mean_ci_empty_is_zero():
    assert mean_ci([]) == (0.0, 0.0, 0.0)


def test_mean_ci_single_value_zero_width():
    assert mean_ci([0.7]) == (0.7, 0.7, 0.7)   # n=1 → SE 0
