"""Move-quality classification: centipawn loss and bucket labels."""


def eval_loss(best_cp: int, result_cp: int) -> int:
    """Centipawns the mover lost by playing their move instead of the best one.

    best_cp is the best score before the move, from the mover's point of view.
    result_cp is the score after the move, from the opponent's point of view,
    so it is negated to bring it back to the mover's perspective. Never negative.
    """
    return max(0, best_cp - (-result_cp))


def bucket(delta: int) -> str:
    """Label a centipawn loss as good, inaccuracy, mistake, or blunder."""
    if delta < 30:
        return "good"
    if delta < 100:
        return "inaccuracy"
    if delta < 300:
        return "mistake"
    return "blunder"
