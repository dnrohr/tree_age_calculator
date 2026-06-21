.PHONY: test fia-data-ne fia-clean-ne fia-train-ne

test:
	python -m unittest discover -s tests -v

fia-data-ne:
	python -m tree_age.fia.cli download

fia-clean-ne:
	python -m tree_age.fia.cli clean

fia-train-ne:
	python -m tree_age.modeling.train data/processed/fia_new_england_clean.csv
