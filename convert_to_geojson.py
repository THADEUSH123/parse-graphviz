#!/usr/bin/python

"""ASPER request to do some fast visualizations with graphviz data."""

from pydot import graph_from_dot_file
from csv import DictReader
from geojson import Feature, Point, LineString, FeatureCollection, dumps
from argparse import ArgumentParser
import string


def load_known_poles(name):
    """Load some pole objects from a csv file."""
    with open(name, 'rb') as csvfile:
        reader = DictReader(csvfile)
        return {row['pole_id']: row for row in reader}


def normalize_edge_name(edge_name):
    """Normalize name based on naming convention in CSV file."""
    if not edge_name.startswith(('_',)):
        edge_name = edge_name.replace('_', '-')
    edge_name = edge_name.replace('_sigplus', '')
    edge_name = edge_name.replace('_vert', '')
    edge_name = edge_name.replace('_lum', '')
    edge_name = edge_name.replace('_sig', '')
    edge_name = edge_name.replace('_either', '')
    edge_name = edge_name.replace('_', '')
    edge_name = edge_name.strip()
    return edge_name

def mounting_style(edge_name):
    if edge_name.endswith(('_sigplus', '_vert', '_lum', '_sig', '_either')):
        return edge_name.rsplit('_', 1)[1]
    return ''

def create_feature(pole_index, name1, name2=None):
    """Create a geojson feature based on imported values."""
    if name2 is None:
        props = pole_index[name1].copy()
        props.update({ 'marker-size' : 'small',
                       "marker-color": "#00f900", # spring green
                       'marker-symbol' : 'circle-stroked',
                       'name' : props['pole_id'] })
        del props['pole_id']
        feature = Feature(
            geometry=Point(
                (float(props['longitude']),
                 float(props['latitude']))),
            properties=props)
    else:
        line_name = pole_index[name1]['pole_id'] + '_' + pole_index[name2]['pole_id']
        feature = Feature(
            geometry=LineString(
                [(float(pole_index[name1]['longitude']),
                 float(pole_index[name1]['latitude'])),
                 (float(pole_index[name2]['longitude']),
                 float(pole_index[name2]['latitude']))]),
            properties={'use': 'unknown',
                        'stroke' : '#fffb00',  # yellow
                        'name' : line_name })

    return feature


def export_to_file(file_name, features):
    """Save the features to a geojson collection formated text file."""
    with open(file_name, 'w')as f:
        f.write(
            dumps(FeatureCollection(
                features=features),
                indent=4, separators=(',', ': ')))

if __name__ == '__main__':
    parser = ArgumentParser(description='graphwiz to geojson.')
    parser.add_argument('-p', '--poles', help='Poles file name')
    parser.add_argument('-g', '--graphviz', help='Graphviz file name')
    parser.add_argument('-o', '--output', help='Output file name')
    args = parser.parse_args()

    poles_file_name = args.poles or 'downtown-pole-export-edited.csv'
    graphviz_file_name = args.graphviz or 'random-graphviz.txt'
    output_file_name = args.output or 'feature-collection-export.json'

    graph = graph_from_dot_file(graphviz_file_name)
    pole_index = load_known_poles(poles_file_name)

    features = {}

    for edge in graph.get_edge_list():
        source = normalize_edge_name(edge.get_source())
        destination = normalize_edge_name(edge.get_destination())
        found_source = source in pole_index.keys()
        found_destination = destination in pole_index.keys()
        if found_source and found_destination:
            pole_index[source]['mounting'] = mounting_style(edge.get_source())
            pole_index[destination]['mounting'] = mounting_style(edge.get_destination())
            features[source + destination] = create_feature(
                                                pole_index,
                                                source,
                                                destination)
            if not source in features:
                features[source] = create_feature(pole_index, source)
            if not destination in features:
                features[destination] = create_feature(pole_index, destination)
        else:
            if not found_source:
                print('Could not find {}'.format(source))
            if not found_destination:
                print('Could not find {}'.format(destination))

    export_to_file(output_file_name, features.values())
