# Video understanding diagnostic fixture

Four independent clip IDs, one frozen run per method, one question per clip.
Primary outcome: exact answer accuracy over clips. The dataset_answer column
is the synthetic dataset annotation, not a prediction-derived reference.
Frames are deterministic toy images supplied at 0, 1 and 2 seconds, aligned
across methods. Only these sparse frames are available. Original continuous
video and audio are unavailable. Do not claim to inspect the absent modalities,
unseen motion between frames or exact event onset within a sampling gap.
A three-frame storyboard is one clip's evidence, not three independent trials.
No additional inference or video reconstruction is authorized.
