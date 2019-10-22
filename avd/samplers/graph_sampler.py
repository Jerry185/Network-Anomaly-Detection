import itertools
import random

import avd.utils.utils as utils


class GraphSampler(object):
    def __init__(self, graph, vertex_min_edge_number, vertex_max_edge_number):
        self._graph = graph
        self._edges = list(graph.edges)
        self._vertices = list(graph.vertices)
        random.shuffle(self._edges)
        random.shuffle(self._vertices)
        self._closed_vertices = set()
        self._vertex_min_edge_number = vertex_min_edge_number
        self._vertex_max_edge_number = vertex_max_edge_number
        self._open_vertices = set(self.get_vertices_with_more_than_n_friends(vertex_min_edge_number,
                                                                             list(self._vertices)))

    def split_training_test_set(self, training_size=None, test_size=None):
        if not training_size:
            training_size = {"neg": 10000, "pos": 10000}
        if not test_size:
            test_size = {"neg": 1000, "pos": 100}
        test_set = self.generate_labeled_sample_by_vertices(test_size["neg"], test_size["pos"])
        training_set = self.generate_sample_for_unlabeled_links(training_size["neg"], training_size["pos"])
        return training_set, test_set

    def get_random_edges_by_vertices(self, edge_number, node_label=False, open_vertices=None):
        """
            Return n edges of randomly chosen vertices

            Parameters
            ----------
            open_vertices
            edge_number : integer
                The number of links that should be extracted and returned.

            node_label : string/integer, optional (default= no attributes)
               Holds the label of the generated edge.

            Returns
            -------
            el : list
                List that contains random edges.
        """
        if not open_vertices:
            open_vertices = []
        node_label = utils.to_iterable(node_label)
        for v_edge in self._edges:
            vertex = v_edge[0]
            if vertex in open_vertices and vertex not in self._closed_vertices:
                if self._graph.get_node_label(vertex) in node_label or False in node_label:
                    self._open_vertices.remove(vertex)
                    self._closed_vertices.add(vertex)
                    for edge in self._graph.get_vertex_edges(vertex, "out"):
                        yield edge
                        edge_number -= 1
                        if not edge_number:
                            break
                    if not edge_number:
                        break

    def get_random_vertices_edges(self, vertices_number, node_label=False):
        """
            Return all edges of n randomly chosen vertices

            Parameters
            ----------
            vertices_number : integer
                The number of vertices that all their links that should be extracted and returned.

            node_label : string/integer, optional (default= no attributes)
               Holds the label of the generated edge.

            Returns
            -------
            el : list
                List that contains random edges.
        """
        node_label = utils.to_iterable(node_label)
        open_vertices = list(self._open_vertices)
        random.shuffle(open_vertices)
        for vertex in open_vertices:
            if self._graph.get_node_label(vertex) in node_label or False in node_label:
                edge_count, temp_edges = 0, []
                for edge in self._graph.get_vertex_edges(vertex, "out"):
                    if edge[1] in self._open_vertices:
                        temp_edges.append(edge)
                        edge_count += 1
                if edge_count > self._vertex_min_edge_number:
                    self._closed_vertices.add(vertex)
                    vertices_number -= 1
                    for edge in temp_edges:
                        yield edge
                if not vertices_number:
                    break
                    # self._open_vertices = self._open_vertices.difference(self._closed_vertices)

    def get_random_vertices_by_edges(self, vertices_number, node_label=False, open_vertices=None):
        """
            Return all edges of n randomly chosen vertices

            Parameters
            ----------
            open_vertices
            vertices_number : integer
                The number of vertices that all their links that should be extracted and returned.

            node_label : string/integer, optional (default= no attributes)
               Holds the label of the generated edge.

            Returns
            -------
            el : list
                List that contains random edges.
        """
        if not open_vertices:
            open_vertices = []
        node_label = utils.to_iterable(node_label)
        random.shuffle(self._edges)
        for v_edge in self._edges:
            vertex = v_edge[0]
            if vertex in open_vertices:
                open_vertices.remove(vertex)
                if self._graph.get_node_label(vertex) in node_label or False in node_label:
                    edge_count, temp_edges = 0, []
                    for edge in self._graph.get_vertex_edges(vertex, "out"):
                        temp_edges.append(edge)
                        edge_count += 1
                    if edge_count > self._vertex_min_edge_number:
                        self._closed_vertices.add(vertex)
                        vertices_number -= 1
                        for edge in temp_edges:
                            yield edge
                    if not vertices_number:
                        break
        self._open_vertices = self._open_vertices.difference(self._closed_vertices)

    def get_random_edge_sample(self, edge_number, selection_label=None):
        """
            Return randomly selected existing edges with specific label.

            Parameters
            ----------
            edge_number : integer
                The number of links that should be generated and returned.
            selection_label : string/integer, optional (default= no attributes)
               Holds the label of the generated edge.

            Returns
            -------
            el : list
                List that contains random edges.
        """
        self._open_vertices = self._open_vertices.difference(self._closed_vertices)
        for edge in self._edges:
            if self._graph.get_edge_label(edge[0], edge[1]) == selection_label:
                if edge[0] in self._open_vertices and edge[1] in self._open_vertices:
                    yield (edge[0], edge[1])
                    self._closed_vertices.add(edge[0])
                    edge_number -= 1
                    if not edge_number:
                        break

    def get_random_vertices(self, vertices_number, selection_label=None, condition=lambda x: True):
        """
            Return randomly selected existing vertices with specific label.

            Parameters
            ----------
            condition
            vertices_number : integer
                The number of vertices that should be generated and returned.
            selection_label : string/integer, optional (default= no attributes)
               Holds the label of the generated edge.

            Returns
            -------
            el : list
                List that contains random edges.
        """
        self._open_vertices = self._open_vertices.difference(self._closed_vertices)
        open_vertices = list(self._open_vertices)
        random.shuffle(open_vertices)
        for vertex in open_vertices:
            if self._graph.get_node_label(vertex) == selection_label or not selection_label:
                if condition(vertex):
                    yield vertex
                    self._closed_vertices.add(vertex)
                    vertices_number -= 1
                    if not vertices_number:
                        break

    def transform_edge(self, edge, selection_label):
        if not self._graph.is_directed:
            selection_label = utils.to_iterable(selection_label)
            if self._graph.get_node_label(edge[0]) not in selection_label:
                return edge[1], edge[0]
        return edge

    def get_vertices_with_more_than_n_friends(self, n, vertices, edge_label=None):
        """
            Return all vertices in the graph that have more than n neighbours.
            Parameters
            ----------
            vertices
            edge_label
            n : integer
                Minimum number of neighbours per node.

            Returns
            -------
            el : list
                List that contains vertices.
        """

        expended_vertices = []
        for vertex in vertices:
            if n < self._graph.get_vertex_out_degree(
                    vertex) < self._vertex_max_edge_number and (
                            self._graph.get_node_label(vertex) == edge_label or edge_label is None):
                expended_vertices.append(vertex)
        return expended_vertices

    def generate_random_edges_with_condition(self, edge_number, is_fit, edge_label=1):
        """
            Return random generated new edges that satisfies give condition .
            We assume that there are labeled positive and negative links in the graph.

            Parameters
            ----------
            edge_number : integer
                The number of links that should be generated and returned.

            is_fit : method pointer
               The method that verifies if edge satisfies the condition.

            edge_label : String/integer, optional (default= 1)
               Holds the label of the generated edge.

            Returns
            -------
            el : list
                List that contains the negative and  positive generated edges.
        """
        new_edges = set()
        open_vertices = list(self._open_vertices)
        while edge_number != len(new_edges):
            v, u = self.get_random_vertex(open_vertices), self.get_random_vertex(open_vertices)
            if is_fit(v, u) and not (v, u, edge_label) in new_edges:
                yield (v, u, edge_label)
                self._closed_vertices.add(v)
                new_edges.add((v, u, edge_label))
        self._open_vertices = self._open_vertices.difference(self._closed_vertices)

    def get_random_vertex(self, open_vertices=None):
        if not open_vertices:
            open_vertices = self._vertices
        return random.choice(open_vertices)

    @staticmethod
    def sample_vertices_by_degree_distribution(graph, n):
        closed_vertices = set()
        edges = list(graph.edges)
        while len(closed_vertices) != n:
            v = random.choice(edges)[0]
            if v not in closed_vertices:
                closed_vertices.add(v)
                yield graph.get_vertex_out_degree(v)

    def is_not_linked(self, v, u):
        return not (self._graph.has_edge(v, u) or self._graph.has_edge(u, v) or v == u)

    def is_in_distance_of_one_hop(self, v, u):
        return self.is_not_linked(v, u) and len(self._graph.get_common_neighbors(v, u)) > 0

    def is_in_distance_of_two_hops(self, v, u):
        dist = self._graph.get_shortest_path_length_with_limit(v, u, 3)[0]
        if u in dist:
            return dist[u] == 3
        return False

    def is_simulated_vertex(self, v):
        return utils.is_attributes_match({"type": "sim"}, self._graph.get_node_attributes(v))

    def is_not_simulated_vertex(self, v):
        return not utils.is_attributes_match({"type": "sim"}, self._graph.get_node_attributes(v))

    def generate_labeled_sample_by_vertices(self, negative_number, positive_number):
        positive_set = self.get_random_vertices_edges(positive_number, self._graph.positive_label)
        negative_set = self.get_random_vertices_edges(negative_number, [None, self._graph.negative_label])
        # negative_set = self.get_random_edges_by_vertices(negative_number, [None, self._graph.negative_label])
        # positive_set = self.get_random_edges_by_vertices(positive_number, self._graph.positive_label)
        return itertools.chain(positive_set, negative_set)

    def generate_sample_for_labeled_links(self, negative_number, positive_number):
        """ Return a sample of edges for an classified graph.
            We assume that there are labeled positive and negative links in the graph.

            Parameters
            ----------
            negative_number : integer
                The number of negative links that should be returned.

            positive_number : integer
               The number of positive links that should be returned.

            Returns
            -------
            el : list
                List that contains the negative and  positive generated edges.
        """
        return itertools.chain(self.get_random_edge_sample(negative_number, self._graph.negative_label),
                               self.get_random_edge_sample(positive_number, self._graph.positive_label))

    def generate_sample_for_unlabeled_links(self, negative_number, positive_number):
        """ Return a sample of edges for an unclassified graph.
            We assume that all links are negative and positives are links that doesn't exists.
            Positive links being randomly generated and returned with the negative.

            Parameters
            ----------
            negative_number : integer
                The number of negative links that should be returned.

            positive_number : integer
               The number of positive links that should be returned.

            Returns
            -------
            el : list
                List that contains the negative and  positive generated edges.
        """
        return itertools.chain(
            self.get_random_edge_sample(negative_number, self._graph.negative_label),
            self.generate_random_edges_with_condition(positive_number, self.is_not_linked,
                                                      edge_label=self._graph.positive_label)
        )

    def generate_sample_for_labeled_vertices(self, negative_number, positive_number):
        """ Return a sample of vertices from the graph.

            Parameters
            ----------
            negative_number : integer
                The number of negative links that should be returned.

            positive_number : integer
               The number of positive links that should be returned.

            Returns
            -------
            el : list
                List that contains the negative and  positive sampled vertices.
        """
        return itertools.chain(
            self.get_random_vertices(positive_number, self._graph.positive_label, self.is_simulated_vertex),
            self.get_random_vertices(negative_number, self._graph.negative_label)
        )

    def generate_sample_for_test_labeled_vertices(self, negative_number, positive_number):
        """ Return a sample of vertices from the graph.

            Parameters
            ----------
            negative_number : integer
                The number of negative links that should be returned.

            positive_number : integer
               The number of positive links that should be returned.

            Returns
            -------
            el : list
                List that contains the negative and  positive sampled vertices.
        """
        return itertools.chain(
            self.get_random_vertices(positive_number, self._graph.positive_label, self.is_not_simulated_vertex),
            self.get_random_vertices(negative_number, self._graph.negative_label)
        )
