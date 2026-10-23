from evaluate import evaluate_matches


def test_offline_evaluation_is_reproducible_and_strong():
    result = evaluate_matches(count=10, seed=11)
    assert result["matches"] == 10
    assert result["planted_stories"] >= 10
    assert result["story_detection_rate"] >= 0.8
    assert result["causal_rejection_rate"] == 1.0
    assert result["correction_acceptance_rate"] == 1.0
