import pandas
import collections


def computeStats(fileName, dl, cols=['ak', 'clink'], header=0, names=None):
    "reads in a csv file with delimiter dl and computes counts on the columns indicated (defaults to 'ak' and 'clink')"
    statDict = collections.OrderedDict()
    df = pandas.read_csv(fileName, delimiter=dl, usecols=cols, header=header, names=names)
    for col in df:
        statDict.update({'Total ' + str(col) + 's: ': getCounts(df, col, False)})
        statDict.update({'Total distinct ' + str(col) + 's: ': getCounts(df, col, True)})

    clink = 'clink' if 'clink' in cols else 'clink' if names and 'clink' in names else None
    ak = 'ak' if 'ak' in cols else 'ak' if names and 'ak' in names else None
    docID = 'docID' if 'docID' in cols else 'docID' if names and 'docID' in names else None

    if clink and ak:
        df['maintained'] = df[clink].str[6] == '0'
        statDict.update({'Total distinct maintained CLINKs: ': getCounts(df[df['maintained'] == True], clink, True)})
        statDict.update({'Total distinct AKs with maintained CLINKs: ': getCounts(df[df['maintained'] == True], ak, True)})

    if docID and ak:
        df['maintained'] = df[docID].str[6:8] != 'ZZ'
        statDict.update({'Total distinct maintained DocIDs: ': getCounts(df[df['maintained'] == True], docID, True)})
        statDict.update({'Total distinct AKs with maintained DocIDs: ': getCounts(df[df['maintained'] == True], ak, True)})

    printStats(statDict)

    return


def printStats(dict):
    for key in dict.keys():
        print(str(key) + "{:,}".format(dict[key]))
    return


def getCounts(df, column, unique=False):
    "Reads dataframe object df and computes stats for column specified. Computes disinct counts if unique = True."
    if unique:
        count = df[column].nunique()
    else:
        count = df[column].count()
    return count
