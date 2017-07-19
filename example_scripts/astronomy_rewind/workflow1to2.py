"""
Prepare astronomy rewind workflows 2a, 2b, and 2c.

1. Cull classificatation file annotations by select question and output
    subject_ids to file
2. Connect to panoptes API though python client and add subject_ids in file to
    new subject set. NOTE: New empty subject set must be created via web
    interface, and ID hardcoded or passed as dict, see cull_subject_ids.__doc__

TO DO:
1. Maybe read username and password from file, not command line
2. Maybe overwrite option is too general, is used for both culling the raw
    classification file and the subject_id files

Usage:
python workflow1to2.py -h
"""

import argparse
import json
import os
import sys

import numpy as np
import pandas as pd

def load_classifications(filename, json_columns=None):
    """
    Load classifications into pandas dataframe, cull only those retired.

    Some columns of the csv are embedded json and need special parsing.
    """
    data = pd.read_csv(filename)

    data["annotations"] = data["annotations"].map(json.loads)
    data["metadata"] = data["metadata"].map(json.loads)
    data["subject_data"] = data["subject_data"].map(json.loads)

    data["annotations"] = unpack(data["annotations"])
    data["subject_data"] = data["subject_data"].map(flatten_subject_info)
    return cull_by_retired(data)


def flatten_subject_info(subject_data):
    """Extract the subject_id from the subject_data."""
    result = list(subject_data.values())[0]
    result.update({'id': list(subject_data.keys())[0]})
    return result


def cull_by_retired(data):
    """Return a copy of a DataFrame with only retired subjects"""
    rets = [i for i in range(len(data))
            if data['subject_data'][i]['retired'] is not None]
    return data.iloc[rets].copy()


def unpack(annotations):
    """
    Return the first value in a series filled with lists.

    All annotations values are lists because of a few multiple tasks.
    The second multiple task always has the value of 'None of the above'
    (For this dataset!!)

    If the second multiple task is not None of the above, nothing will happen.
    """
    retv = annotations
    long = [i for i in range(len(annotations)) if len(annotations.iloc[i]) > 1]
    try:
        longval, = np.unique([annotations.iloc[l][1]['value'] for l in long])
        if longval == 'None of the above':
            retv = [a[0] for a in annotations]
        else:
            print('might have important information in annotation list')
    except ValueError:
        print('can not unpack annotations')
        retv = annotations
    return retv


def explore(annotations):
    """
    print the values that are in the annotations
        'A single sky\xa0figure *with* axes labeled',
        'An illustration not directly of the sky',
        'Graph',
        'Graph(s)',
        'Illustration(s) not directly of the sky',
        'Sky figure(s) *without* axes labeled',
        'Surface imaging of a solar system object',
        'Table',
        'Table(s)',
        'Two or more sky figures *with* axes labeled'
    """
    values = np.unique(np.concatenate([a['value'] for a in annotations]))
    print(values)
    return values


def cull_subject_ids(filename, w2s=None, overwrite=False, add=False,
                     subject_set_ids=None, add_kw=None):
    """
    Cull classifications file and write to new workflows.

    Parameters
    ----------
    filename : str
        input csv file

    ws2 : dict
        key: workflow title (for file naming)
        value: Single string to select on within annotations values.

    overwrite : bool [False]
        overwrite with new file

    add : bool
        call add_to_subject_set

    subject_set_ids : dict
        key: must match ws2.keys
        value: Empty set IDs already created on the web interface

    add_kw : dict
        kwargs passed to add_to_subject_set if add is True
    """
    add_kw = add_kw or {}
    # load and munge data
    data = load_classifications(filename)

    if w2s is None:
        # see, e.g., explore(data)
        w2s = {'2a': 'A single sky\xa0figure *with* axes labeled',
               '2b': 'Two or more sky figures *with* axes labeled',
               '2c': 'Sky figure(s) *without* axes labeled'}
        # Empty set IDs already created on the web interface
        #subject_set_ids = {'2a': 12651,
        #                   '2b': 8433,
        #                   '2c': 12645}
        subject_set_ids = {'2a': 13405,
                           '2b': 13406,
                           '2c': 13407}

    for wf in w2s.keys():
        # new filename assumes wf1 is in the first filename!
        outname = filename.replace('classifications_wf1',
                                   'subject_ids_wf{0:s}'.format(wf))

        # Identifiy matches to next workflow
        # allowing widest range of answers, so multiple answers included.
        iwf = [w2s[wf] in a['value'] for a in data['annotations']]

        # create sub-copy of dataframe with only workflow matches
        df = data['subject_ids'].iloc[iwf]

        # write ... or not
        if not os.path.isfile(outname) or overwrite:
            df.to_csv(outname, index=False)
            msg = 'wrote'
        else:
            msg = 'not overwriting'
        print('{0:s} {1:s}'.format(msg, outname))

        if add:
            add_to_subject_set(subject_set_ids[wf], outname, **add_kw)
    return


def add_to_subject_set(subject_set_id, subject_set_file, username=None,
                       password=None):
    """
    Import a 1 column file of subject_ids to a subject_set.

    Parameters
    ----------
    subject_set_id : str
        subject set ID linked to the web interface

    subject_set_file : str
        one-column file of subject IDs (output of cull_subject_ids)

    username, password : str, str
        if passed, will add subject set ids to the subject set on the web.
    """
    lines = []
    with open(subject_set_file) as subject_ids:
        lines.append(subject_ids.read().splitlines())

    if username is not None:
        try:
            from panoptes_client import Panoptes, SubjectSet
        except ImportError:
            print('Install https://github.com/zooniverse/panoptes-python-client')
            sys.exit(1)

        Panoptes.connect(username=username, password=password)
        subject_set = SubjectSet.find(subject_set_id)
        subject_set.add(np.unique(lines))
    return


def cull_export_by_workflow(filename, workflow_id=1701, id='wf1'):
    """
    Cull exported (from zooniverse) csv by one workflow_id.

    Parameters
    ----------
    filename : str
        classifications filename
    workflow_id : int
        workflow_id number
    id : str
        string to add to the filename extension to write a new file

    Returns
    -------
    newname : str
        culled file with the id added before the extension separated by '_'.
    """
    name, ext = os.path.splitext(filename)
    newname = '{}_{}{}'.format(name, id, ext)

    subjs = pd.read_csv(filename)
    iwf1 = np.nonzero(subjs.workflow_id == workflow_id)
    df = subjs.iloc[iwf1]
    df.to_csv(newname, index=False)
    return newname


def main(argv=None):
    """Main caller for workflow1to2"""
    parser = argparse.ArgumentParser(
        description="Add subject sets to workflow 2a,b,c from classifications")

    parser.add_argument('username', type=str, help='zooniverse username')

    parser.add_argument('password', type=str, help='password')

    parser.add_argument('-o', '--overwrite', action='store_true')
    parser.add_argument('-a', '--add', action='store_true')

    args = parser.parse_args(argv)

    # hard coded so others won't try to run this on their data without a deep
    # dive.
    classification_file = 'astronomy-rewind-classifications.csv'

    wf1_filename = cull_export_by_workflow(classification_file)
    cull_subject_ids(wf1_filename, overwrite=args.overwrite, add=args.add,
                     add_kw={'username': args.username,
                             'password': args.password})


if __name__ == "__main__":
    sys.exit(main())
