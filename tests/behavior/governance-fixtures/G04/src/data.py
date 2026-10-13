"""Shared batch: x float[B,1], y int[B], ids int[B]. Label mapping 0/1; no I/O.

get_batch() returns the same fixed training IDs for every method.
"""
def get_batch():
    return [[-2.0],[0.0],[2.0]], [0,1,0], [10,11,12]
