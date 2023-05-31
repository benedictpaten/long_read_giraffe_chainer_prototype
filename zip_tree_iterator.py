
"""
Example zip tree - here the grammar is:

    zip_tree -> chain
                snarl

    chain -> [ elements ]

    elements -> element
             -> element distance elements

    element -> seed
            -> snarl

    snarl -> ( chains ( distances_to_previous_N_chains ) )

    chains -> ( distances_to_previous_N_chains chain )
           -> ( distances_to_previous_N_chains chain ) chains

    distances_to_previous_N_chains -> integer x (N+1), where N is the number of preceding chains in the net,
    each integer is the distance to the preceding chains in the snarl, as specified from left-to-right,
    with the first integer being the distance to the left boundary node, i.e. for ( ( a [x] ) ( b c [y] ) ( d e f )),
    a is the distance from the left side of the x chain to the left snarl boundary,
    b is the distance from the left side of y to the left snarl boundary, c is the distance from the left side of
    y to the right side of x, d is the distance from the right snarl boundary to the left snarl boundary,
    e is the distance from the right snarl boundary to the right side of x and f is the distance from the
    right snarl boundary to the right side of y.
"""
zip_tree = ["a", 5, ((1, ["b"]), (1, 0)), 10, "c", 4, "d", 3,
            ((2, ["e", 4, ((2, ["f"]), (3, 0)), 6, "g"]), (4, 2, ["h"]), (1, 2, 1)), 7, "i", 2, "j"]


def zip_element_right_to_left_iterator(element, max_distance):
    """ Iterator over seeds in zip tree in right-to-left order.

    Returned values are each a tuple of (seed, min-distance-to-the-right)
    where min-distance-to-the-right is the distance from the seed to the right end of the zip tree.

    Will not return seeds further than max_distance apart."""

    # If the element we are searching from is a snarl
    if isinstance(element, ().__class__):

        # Walk back through the sub-elements in the snarl from right-to-left
        for i in range(len(element)-2, -1, -1):

            # Recursively call the zip_iterator to look at the elements in the nested sub-element
            for seed, nested_distance in zip_element_right_to_left_iterator(element[i][-1], max_distance):

                d = nested_distance + element[-1][i+1]  # This is the distance from the nested element to the
                # right snarl boundary node

                if d <= max_distance: # Only return pair if less than the max distance
                    yield seed, d

    # If the element we are searching from is a chain
    elif isinstance(element, [].__class__):

        # Minimum distance to the rightmost seed in the chain
        distance_from_right_chain_end = 0

        for i in range(len(element)-1, -1, -2):  # Walk back through the sub-elements in the chain from right-to-left
            nested_element = element[i]

            # Following logic is same as snarl case above
            for seed, nested_distance in zip_element_right_to_left_iterator(nested_element, max_distance):
                d = nested_distance + distance_from_right_chain_end

                if d <= max_distance: # Only return pair if less than the max distance
                    yield seed, d

            if isinstance(nested_element, ().__class__):  # If the nested element is a snarl, add the minimum
                # distance across it
                distance_from_right_chain_end += nested_element[-1][0]

            if i > 0:  # If we have not reached the end of the chain, add the next distance along
                # the chain to the running sum, distance_from_right_chain_end
                distance_from_right_chain_end += element[i-1]

            if distance_from_right_chain_end > max_distance:  # If min distance exceeds threshold, we're done
                return

    # If the element we are searching from is a seed
    else:
        yield element, 0


def zip_element_left_to_right_iterator(element):
    """ Iterator over seeds in zip tree in left-to-right order.

    Returned values are each a pair of (seed, contained-elements)
    where  contained-elements is a list, from left-to-right of the deepest to
    shallowest snarls/chains containing the seed."""

    # If the element we are searching from is a snarl
    if isinstance(element, ().__class__):

        # Walk back through the sub-elements in the snarl from right-to-left
        for i in range(0, len(element)-1):

            # Recursively call the zip_iterator to look at the elements in the nested sub-element
            for seed, contained_elements in zip_element_left_to_right_iterator(element[i][-1]):

                c = contained_elements + [element, i]  # The contained elements is a list which goes, left-to-right
                # from deepest to shallowest of the snarls/chains containing the seed

                yield seed, c

    # If the element we are searching from is a chain
    elif isinstance(element, [].__class__):

        for i in range(0, len(element), 2):  # Walk back through the sub-elements in the chain from right-to-left
            nested_element = element[i]

            # Following logic is same as snarl case above
            for seed, contained_elements in zip_element_left_to_right_iterator(nested_element):
                yield seed, contained_elements + [element, i]

    # If the element we are searching from is a seed
    else:
        yield element, []


def zip_reachable_iterator(contained_elements, max_distance):
    """ Iterator over the seeds reachable from a given seed, defined by a set of contained elements, each
    either a snarl or chain, that contain the seed that is being iterated from.

    Will not report seeds that are more than max_distance away.
    """
    # The distance from the seed to the snarl / chain we are traversing
    distance_from_right = 0

    # For each snarl or chain containing the seed, from deepest to top-level
    for i in range(0, len(contained_elements), 2):
        element = contained_elements[i]  # The snarl or chain
        j = contained_elements[i+1]  # The index that the seed occurs within the snarl / chain

        # If the seed we are searching from is in a snarl
        if isinstance(element, ().__class__):

            # Walk back through the chains in the snarl from right-to-left, starting from chain before the chain
            # containing the seed
            for k in range(j-1, -1, -1):

                # Recursively call the zip_iterator to look at the seeds nested within the preceding chain
                for seed, nested_distance in zip_element_right_to_left_iterator(element[k][-1], max_distance):

                    # Calculate the distance to the nested seed
                    # element[j][k + 1] is the distance to the chain
                    # distance from the right is the distance to the snarl containing the chain
                    d = nested_distance + element[j][k + 1] + distance_from_right

                    if d <= max_distance:  # Only return pair if less than the max distance
                        yield seed, d

            # Add the minimum distance through the snarl to the distance we traverse to the seed
            distance_from_right += element[j][0]

            # Stop reporting if the distance on any further reachable seed will exceed the max_distance
            if distance_from_right > max_distance:
                return

        # Else the seed we are searching from is in a chain
        else:
            assert isinstance(element, [].__class__)

            # Walk back through the sub-elements in the chain from right-to-left
            for k in range(j - 2, -1, -2):

                # Add to the distance from the element we're iterating from
                distance_from_right += element[k + 1]

                # Stop if we exceed the max_distance
                if distance_from_right > max_distance:
                    return

                # Recursively call the zip_iterator to look at the elements in the nested sub-element
                for seed, nested_distance in zip_element_right_to_left_iterator(element[k], max_distance):

                    # Calculate the distance to the nested seed
                    d = nested_distance + distance_from_right

                    if d <= max_distance:  # Only return pair if less than the max distance
                        yield seed, d

                if isinstance(element[k], ().__class__):  # If the nested element is a snarl, add the minimum
                    # distance across it
                    distance_from_right += element[k][-1][0]

                # Again, stop if we exceed the max_distance
                if distance_from_right > max_distance:
                    return


def zip_element_pairs_iterator(zip_tree, max_distance):
    """ Iterator that reports all the pairs of distances between seeds in the tree.
    Will not report distances longer than max_distance. """

    # For each seed from left-to-right across the snarl tree
    for element, contained_elements in zip_element_left_to_right_iterator(zip_tree):

        # For each seed reachable from the seed
        for element2, distance in zip_reachable_iterator(contained_elements, max_distance):
            yield element, element2, distance  # Report the pair and the distance


# First, demo iterating over seeds in right-to-left order
print("Seeds in right-to-left order")
for element, distance_to_right in zip_element_right_to_left_iterator(zip_tree, 1000):
    print("Element:", element, "Distance to right end:", distance_to_right)

# Second, demo iterating over seeds in right-to-left order
print("Seeds in left-to-right order")
for element, contained_elements in zip_element_left_to_right_iterator(zip_tree):
    print("Element:", element)

# Now report all the pairs of distances
print("\nAll pairs of distances <= 15")
for element, element2, distance in zip_element_pairs_iterator(zip_tree, 15):
    print("Element_to:", element, "Element_from:", element2, "Distance", distance)