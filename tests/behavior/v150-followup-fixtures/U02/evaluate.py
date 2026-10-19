"""Compute accuracy against the saved targets for one named prediction field."""


def accuracy(rows, field):
    return sum(row[field] == row['target'] for row in rows) / len(rows)
