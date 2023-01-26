
import os
from pathlib import Path
import re
from shutil import copyfile
from tomlkit import parse as parse_toml


def find(key, value):
    for k, v in value.items():
        if k == key:
            yield v
        elif isinstance(v, dict):
            for result in find(key, v):
                yield result
        elif isinstance(v, list):
            for d in v:
                for result in find(key, d):
                    yield result


def convert_dict_values_to_str(matches):
    for key, value in matches.items():
        if isinstance(value, dict):
            matches[key] = str(value)    
    return matches


def multiple_replace(dict, text):
    regex = re.compile("(%s)" % "|".join(map(re.escape, dict.keys())))
    text_replace = regex.sub(lambda mo: dict[mo.string[mo.start():mo.end()]], text)
    return text_replace


def create_dags_file(configs):
    dags_id = [key for key in configs['dags'].keys() if key != 'default']
    dag_folder = configs['dags']['default']['folder']
    template = os.path.normpath(configs['dags']['default']['template'])
    dags_file_name = [os.path.normpath(dag_folder + dag_id + ".py") for dag_id in dags_id]
    [copyfile(template, dag_file_name) for dag_file_name in dags_file_name]
    return dags_file_name


def parse_datasets_upstream(configs):
    upstreams = list(find('dataset_upstream', configs))
    upstreams_split = [re.sub(r'[\[\]\s]', '', x).split(',') for x in upstreams]
    upstream_code = [['Dataset(' + y + ')' for y in x] for x in upstreams_split]
    code_without_marks = [re.sub(r'\"', '', str(x)) for x in upstream_code]
    upstreams_to_replace = dict(zip(upstreams, code_without_marks))
    return upstreams_to_replace


configs_file = Path('/home/airflow/airflow/include/dags_config/').glob('**/*.toml')
for config_file in configs_file:
    configs = parse_toml(Path(str(config_file)).read_text())
    dags_file = create_dags_file(configs)
    py_content = Path(configs['dags']['default']['template']).read_text()

    matches_from_py_template = re.findall(r'\$\{[a-zA-Z\_]+\}', py_content)
    matches_without_placeholders = [re.sub(r'[\$\{\}]', '', match) for match in matches_from_py_template]
    matches_value = [list(find(match, configs)) for match in matches_without_placeholders]

    #TODO: se tiver alguma não correspondência, ou seja, algum valor do matches_value for nulo
    # o unpacking anulará todos os registros. Corrigir isso!
    matches_value_unpacking = zip(*matches_value)

    matches_with_value = [dict(zip(matches_from_py_template, value)) for value in matches_value_unpacking]
    matches_with_value_dict_to_str = map(convert_dict_values_to_str, matches_with_value)
    replaced_py_contents = list(map(lambda matches: multiple_replace(matches, py_content), matches_with_value_dict_to_str))
    datasets_upstream = parse_datasets_upstream(configs)
    py_contents_dataset = list(map(lambda text: multiple_replace(datasets_upstream, text), replaced_py_contents)) if bool(datasets_upstream) else replaced_py_contents
    for (dag_file, py_content_dataset) in zip(dags_file, py_contents_dataset):
        with open(dag_file, "w") as file: 
            file.write(py_content_dataset)


