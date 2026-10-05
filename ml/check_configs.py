from datasets import load_dataset

configs = ['default', 'color', 'segmented', 'grayscale']
for config in configs:
    try:
        ds = load_dataset('mohanty/PlantVillage', config)
        print(f'Config: {config}')
        print(f'  Features: {ds["train"].features}')
        print(f'  Train size: {len(ds["train"])}')
        print(f'  Test size: {len(ds["test"])}')
        print()
    except Exception as e:
        print(f'Config {config} failed: {e}')
        print()