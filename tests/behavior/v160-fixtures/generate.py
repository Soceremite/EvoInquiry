"""Public synthetic fixtures; no general research or optimizer claim."""
import random, math

def data(seed):
    rng=random.Random(seed)
    return [(rng.uniform(-2,2),rng.gauss(0,.08)) for _ in range(400)]

def fit(rows, quadratic=False):
    features=[([1,x,x*x] if quadratic else [1,x]) for x,y in rows]
    n=len(features[0]); matrix=[[sum(v[i]*v[j] for v in features) for j in range(n)] for i in range(n)]
    rhs=[sum(v[i]*row[1] for v,row in zip(features,rows)) for i in range(n)]
    for i in range(n):
        pivot=matrix[i][i]
        for j in range(i,n): matrix[i][j]/=pivot
        rhs[i]/=pivot
        for k in range(n):
            if k==i: continue
            factor=matrix[k][i]
            for j in range(i,n): matrix[k][j]-=factor*matrix[i][j]
            rhs[k]-=factor*rhs[i]
    return rhs

def rmse(rows, weights, offset=0):
    return math.sqrt(sum((sum(w*x**i for i,w in enumerate(weights))+offset-y)**2 for x,y in rows)/len(rows))


def generate(output):
    """Recreate the two synthetic result tables; no LLM selects any decision."""
    from pathlib import Path
    import csv
    output = Path(output)
    for case in ('T01', 'T02'):
        destination = output / case
        destination.mkdir(parents=True, exist_ok=True)
        rows = []
        for seed in range(5):
            samples = data(seed)
            for group in ('A', 'B'):
                quadratic = case == 'T02' and group == 'B'
                train = [(x, (x*x if quadratic else 2*x)+noise) for x, noise in samples[:250]]
                test = [(x, (x*x if quadratic else 2*x)+noise) for x, noise in samples[250:]]
                for variant in ('baseline', 'more_training', 'center_intervention', 'feature_intervention'):
                    weights = fit(train, quadratic=quadratic and variant == 'feature_intervention')
                    offset = .6 if case == 'T01' or group == 'A' else 0
                    if variant == 'center_intervention':
                        offset = 0
                    rows.append({'seed':seed, 'group':group, 'variant':variant,
                                 'rmse':rmse(test, weights, offset), 'n_test':150})
        with (destination/'results.csv').open('w', newline='', encoding='utf-8') as handle:
            writer = csv.DictWriter(handle, fieldnames=rows[0])
            writer.writeheader()
            writer.writerows(rows)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    generate(parser.parse_args().output)
