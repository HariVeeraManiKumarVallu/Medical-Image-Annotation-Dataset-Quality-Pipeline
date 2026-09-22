.PHONY: nih chest_condition test clean

nih:
	python -m src.nih_sample.run_pipeline --config configs/nih_sample.yaml

chest_condition:
	python -m src.chest_condition.run_pipeline --config configs/chest_condition.yaml

test:
	python -m pytest -q

clean:
	python -c "from pathlib import Path; [p.unlink() for p in Path('data').rglob('*.csv') if p.parts[-2] == 'processed']"