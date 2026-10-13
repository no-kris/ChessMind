import pytest

from app.services.classify import bucket, eval_loss


@pytest.mark.parametrize(
    ("delta", "label"),
    [
        (29, "good"),
        (30, "inaccuracy"),
        (99, "inaccuracy"),
        (100, "mistake"),
        (299, "mistake"),
        (300, "blunder"),
    ],
)
def test_bucket_boundaries(delta, label):
    assert bucket(delta) == label


def test_best_move_loses_nothing():
    assert eval_loss(50, -50) == 0


def test_score_flips_to_mover_perspective():
    assert eval_loss(100, 200) == 300


def test_missing_checkmate_is_blunder():
    assert bucket(eval_loss(10000, 0)) == "blunder"


def test_loss_is_never_negative():
    assert eval_loss(50, -60) == 0
