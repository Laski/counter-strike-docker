import pytest
from pyannotate_runtime import collect_types

if __name__ == '__main__':
    collect_types.init_types_collection()
    with collect_types.collect():
        pytest.main()
    collect_types.dump_stats('type_info.json')
