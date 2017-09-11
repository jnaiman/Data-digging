"""Utils to double check workflow1to2 """
import pandas as pd
from workflow1to2 import cull_export_by_workflow


def filter_subject_export_by_wf2():
    """combine the subjects export with the workflow subject ids"""
    cull_export_by_workflow('astronomy-rewind-subjects.csv')
    subjs = pd.read_csv('astronomy-rewind-subjects_wf1.csv')
    wf2names = ['astronomy-rewind-subject_ids_wf2a.csv',
                'astronomy-rewind-subject_ids_wf2b.csv',
                'astronomy-rewind-subject_ids_wf2c.csv']
    for wf2name in wf2names:
        newname = wf2name.replace('_ids', 's')
        wf2 = pd.read_csv(wf2name, names=['subject_id'])
        wf2s = pd.merge(subjs, wf2, on='subject_id')
        wf2s.to_csv(newname, index=False)
    return


def unpack_dict(locations_data):
    return list(locations_data.values())[0]


def imgstr(imgloc):
    """html img tag"""
    istr = ('<div style="display: block; text-align: left;">'
            '<a href="{0}"><img src="{0}" border="0" height="200"></a></div>')
    return istr.format(imgloc)


# More HTML garbage
hdr = ('<table border="1" bordercolor="#888" cellspacing="0" '
       'style="border-collapse: collapse; border-color: rgb(136, 136, 136); '
       'border-width: 1px;">\n<tbody>')
rowstr = ('<tr><td>{0:s}</td></tr>\n'
          '<tr><td>{1:s}</td></tr>\n'
          '<tr><td>{2:d}</td></tr>\n')
ftr = '</tbody>\n</table>\n<br>\n'


def subject_ids_to_html_table(subjects_file):
    """
    Don't do this.

    That is, make a html table that loads all the images of a workflow.
    """
    subjs = pd.read_csv(subjects_file)
    subjs["locations"] = subjs["locations"].map(json.loads)
    subjs["metadata"] = subjs["metadata"].map(json.loads)
    subjs["locations"] = subjs["locations"].map(unpack_dict)

    line = hdr
    u, inds = np.unique(subjs['subject_id'], return_index=True)
    for i in inds:
        row = subjs.iloc[i]
        try:
            title = row['metadata']['title']
        except KeyError:
            title = row['metadata']['Title']
        line += rowstr.format(title,
                              imgstr(row['locations']),
                              row['subject_id'])
    line += ftr
    name, ext = os.path.splitext(subjects_file)
    newname = '{}.html'.format(name)
    with open(newname, 'w') as outp:
        outp.write(line)

if __name__ == '__main__':
    filter_subject_export_by_wf2()
