# coding=utf-8
""" Some util functions """

from copy import deepcopy
import ee
from .tools import string
import threading


def getReducerName(reducer):
    """
    Get the name of the parsed reducer.

    WARNING: This function makes a request to EE Servers (getInfo). Do not use
    in server side functions (example: inside a mapping function)
    """
    reducer_type = reducer.getInfo()['type']

    relations = dict(
        mean=['Reducer.mean', 'Reducer.intervalMean'],
        median=['Reducer.median'],
        mode=['Reducer.mode'],
        first=['Reducer.first', 'Reducer.firstNonNull'],
        last=['Reducer.last', 'Reducer.lastNonNull'],
        stdDev=['Reducer.stdDev', 'Reducer.sampleStdDev'],
        all=['Reducer.allNoneZero'],
        any=['Reducer.anyNoneZero'],
        count=['Reducer.count', 'Reducer.countDistinct'],
        max=['Reducer.max'],
        min=['Reducer.min'],
        product=['Reducer.product'],
        variance=['Reducer.sampleVariance', 'Reducer.variance'],
        skew=['Reducer.skew'],
        sum=['Reducer.sum']
    )

    for name, options in relations.items():
        if reducer_type in options:
            return name


def castImage(value):
    """ Cast a value into an ee.Image if it is not already """
    if isinstance(value, ee.Image) or value is None:
        return value
    else:
        return ee.Image.constant(value)


def makeName(img, pattern, date_pattern=None, extra=None):
    """ Make a name with the given pattern. The pattern must contain the
    propeties to replace between curly braces. There are 2 special words:

    * 'system_date': replace with the date of the image formatted with
      `date_pattern`, which defaults to 'yyyyMMdd'
    * 'id' or 'ID': the image id. If None, it'll be replaced with 'id'

    Pattern example (supposing each image has a property called `city`):
    'image from {city} on {system_date}'

    You can add extra parameters using keyword `extra`
    """
    img = ee.Image(img)
    props = img.toDictionary()
    props = ee.Dictionary(ee.Algorithms.If(
        img.id(),
        props.set('id', img.id()).set('ID', img.id()),
        props))
    props = ee.Dictionary(ee.Algorithms.If(
        img.propertyNames().contains('system:time_start'),
        props.set('system_date', img.date().format(date_pattern)),
        props))
    if extra:
        extra = ee.Dictionary(extra)
        props = props.combine(extra)
    name = string.format(pattern, props)

    return name


def maskIslands(mask, limit, pixels_limit=1000):
    """ returns a new mask where connected pixels with less than the 'limit'
    of area are turned to 0 """
    area = ee.Image.pixelArea().rename('area')

    conn = mask.connectedPixelCount(pixels_limit).rename('connected')
    finalarea = area.multiply(conn)

    # get holes and islands
    island = mask.eq(1).And(finalarea.lte(limit))

    # get rid island
    no_island = mask.where(island, 0)

    return no_island


def dict2namedtuple(thedict, name='NamedDict'):
    """ Create a namedtuple from a dict object. It handles nested dicts. If
    you want to scape this behaviour the dict must be placed into a list as its
    unique element """
    from collections import namedtuple

    thenametuple = namedtuple(name, [])

    for key, val in thedict.items():
        if not isinstance(key, str):
            msg = 'dict keys must be strings not {}'
            raise ValueError(msg.format(key.__class__))

        if not isinstance(val, dict):
            # workaround to include a dict as an attribute
            if isinstance(val, list):
                if isinstance(val[0], dict):
                    val = val[0]

            setattr(thenametuple, key, val)
        else:
            newname = dict2namedtuple(val, key)
            setattr(thenametuple, key, newname)

    return thenametuple


def formatVisParams(visParams):
    """ format visualization parameters to match EE requirements at
    ee.data.getMapId """
    formatted = dict()
    for param, value in visParams.items():
        if isinstance(value, list):
            value = [str(v) for v in value]
        if param in ['bands', 'palette']:
            formatted[param] = ','.join(value) if len(value) == 3 else str(value[0])
        if param in ['min', 'max', 'gain', 'bias', 'gamma']:
            formatted[param] = str(value) if isinstance(value, (int, str)) else ','.join(value)
    return formatted


def _retrieve(f):
    def wrap(obj, *args):
        f(obj.getInfo(), *args)
    return wrap


def evaluate(obj, callback, args):
    """ Retrieve eeobject value asynchronously. First argument of callback
    must always be the object itself """
    args.insert(0, obj)
    callback = _retrieve(callback)
    thd = threading.Thread(target=callback, args=args)
    thd.start()
