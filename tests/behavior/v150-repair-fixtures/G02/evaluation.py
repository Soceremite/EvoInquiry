def evaluate(rows):
    correct_tokens = sum(sum(a == b for a, b in zip(r["target"], r["predicted"])) for r in rows)
    total_tokens = sum(len(r["target"]) for r in rows)
    successes = sum(all(r["target"][i] == r["predicted"][i] for i in r["masked_positions"]) for r in rows)
    return {"token_accuracy": correct_tokens / total_tokens,
            "masked_exact": successes / len(rows), "eligible": len(rows), "successes": successes}
