import importlib.util
from pathlib import Path
import pytest

SPEC=importlib.util.spec_from_file_location('mcs_cells',Path(__file__).resolve().parents[2]/'scripts/prepare-mcs-final-key-mappings.py')
CELLS=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(CELLS)


def test_text_table_keeps_printed_numbers_and_excludes_compensation():
    text='\n'.join(f'{i} (C)' for i in range(1,101)if i!=43)
    answers=CELLS.parse_text_key(text,[43]);assert len(answers)==99 and answers[44]=='C'and 43 not in answers
    for invalid in [text+'\n44 (A)',text.replace('44 (C)','44 OCR error')]:
        with pytest.raises(ValueError):CELLS.parse_text_key(invalid,[43])


def test_image_table_requires_exact_columns_and_compensated_positions():
    values=['A']*100;values[36]='X';page={'rows':[' '.join(values[n:n+25])for n in range(0,100,25)]}
    answers=CELLS.parse_image_key(page,[37]);assert len(answers)==99 and 37 not in answers
    with pytest.raises(ValueError):CELLS.parse_image_key(page,[38])
    with pytest.raises(ValueError):CELLS.parse_image_key({'rows':['A '*25]*3},[])
    with pytest.raises(ValueError):CELLS.parse_image_key({'rows':['Z '+'A '*24]+['A '*25]*3},[])
