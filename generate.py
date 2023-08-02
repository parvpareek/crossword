import sys

from queue import Queue
from crossword import *
import copy


class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        _, _, w, h = draw.textbbox((0, 0), letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        Update `self.domains` such that each variable is node-consistent.
        (Remove any values that are inconsistent with a variable's unary
         constraints; in this case, the length of the word.)
        """
        # Iterate through every variable
        for var in self.domains:
            invalid_words = []
            # Iterate through the every word in the set mapped to the variable
            for word in self.domains[var]:
                # If length of variable does not match the length of domain word, remove it
                if var.length != len(word):
                    # Add it to separate list and remove it later so that the set doesnt change under execution
                    invalid_words.append(word)

            for word in invalid_words:
                # Remove every invalid word in the domain
                self.domains[var].remove(word)

    def revise(self, x, y):
        """
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.

        Return True if a revision was made to the domain of `x`; return
        False if no revision was made.
        """
        # Set revised to False by default
        revised = False
        # Get the cell where the two variables intersect
        i, j = self.crossword.overlaps[x, y]
        
        """ 
        # If there is no intersection return False
        if intersection is None:
            return False"""
        
        invalid_words = set()
        # Iterate through every word in X's domain
        for x_word in self.domains[x]:
            # By default lets assume that there are no possible words
            possible = False
            # Iterate through every word in Y's domain for every x_word
            for y_word in self.domains[y]:
                # If there is a compatible word present for the given x_word(It satisfies the constraint of common cell)
                if x_word[i] == y_word[j]:
                    # There is a word possible so break the loop
                    possible = True
                    break
            # If there are no possible words in y's domain then remove that word from x's domain and set revised as
            if not possible:
                invalid_words.add(x_word)

        for x_word in invalid_words:
            self.domains[x].remove(x_word)
            revised = True

        
        return revised

    def ac3(self, arcs=None):
        """
        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.

        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.
        """
        queue = Queue()
        # If the list is empty add all possible arcs between two variables
        if arcs is None:
            for x in self.crossword.variables:
                for y in self.crossword.variables:
                    if x != y and self.crossword.overlaps[x, y]:

                        queue.put((x, y))
        # IF there is arcs' list given then add them in the queue 
        if arcs is not None:
            for arc in arcs:
                queue.put(arc)
        
        
        
        while not queue.empty():
            (x, y) = queue.get()

            changes = self.revise(x, y)

            if changes:
                if len(self.domains[x]) == 0:
                    return False
                # If changes were made to x's domain, find neighbours of x
                neighbours = self.crossword.neighbors(x)

                # remove y from neighbours because thats the specification
                neighbours.remove(y)

                # add arcs of x and its neighbours to the queue to maintain arc consistency after changes were made to x
                for var in neighbours:
                    queue.put((var, x))
        return True





    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """
        """complete = True
        for var in assignment:
            if assignment[var] is None or assignment[var] == "":
                complete = False"""

        return len(assignment) == len(self.crossword.variables) 

    def consistent(self, assignment):
        """
        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.
        """
        # check for unique values
        words = set(assignment.values())
        if len(words) != len(assignment.keys()):
            return False
        
        # Check if the length of value is correct
        for var in assignment:

            # For length
            if var.length != len(assignment[var]):
                return False
            

            # For conflicting values
            neighbours = self.crossword.neighbors(var)

            # IF there are no nieghbours return True
            if len(neighbours) == 0:
                return True

            for neighbour in neighbours:
                if neighbour in assignment:
                    x, y = self.crossword.overlaps[var, neighbour]
                    if assignment[var][x] != assignment[neighbour][y]:  
                        return False


        return True


    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """
        # All the assigned variable i dont need to consider
        assigned_vars = set(assignment.keys())
        # Set of all  neighours or var that are unassigned
        neighbours = set(self.crossword.neighbors(var)) - assigned_vars

        #List of all possible values ordered in ascending order of constraint
        constraint_list = []
        constraint_dict = {}

        # Loop through the domain    
        for value in self.domains[var]:
            n = 0
            # loop through each neighbour
            for neighbour in neighbours:
                # If the value is also present in the neighbour's domain
                if value in self.domains[neighbour]:
                    n += 1

            # Store the constraining value in a dictionary
            constraint_dict[value] = n        

        constraint_list = [k for k, v in sorted(constraint_dict.items(), key=lambda item: item[1])]
        return constraint_list
        

        

    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """
        x = []
        ordered_variables  = []
        # Get set of assigned variables
        assigned_variables = set(assignment.keys())
        #Iterate through set of unassigned variables
        for variable in self.crossword.variables - assigned_variables:
            # Append the variable, possible values available and neighbours
            x.append((variable, len(self.domains[variable]), len(self.crossword.neighbors(variable))))

        ordered_variables = [k for (k, d, n) in sorted(x, key=lambda x: (x[1], -x[2]))]
        return ordered_variables[0]


    def backtrack(self, assignment):
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.

        `assignment` is a mapping from variables (keys) to words (values).

        If no assignment is possible, return None.
        """
        # Base case at the end of recursion if assignment is complete return it
        if self.assignment_complete(assignment):
            return assignment

        variable = self.select_unassigned_variable(assignment)

        for value in self.order_domain_values(variable, assignment):

            # Create a copy of assignment and domains for backtracking
            assignment_copy = assignment.copy()
            domain_copy = copy.deepcopy(self.domains)

            # If the assignment of the value is consistent
            if self.consistent(assignment | {variable: value}):
                # Add {var=value} to assignment and update domain
                assignment[variable] = value 
                self.domains[variable] = {value}

                inferences = self.inference(variable, assignment)
                # If arc consistent is not mainained after the assignment

                if not inferences:
                    return None

                # Storing the result of backtrack
                result = self.backtrack(assignment)

                # If the result is not null, that means assignment was succestfull and we return it
                if result is not None:
                    return result

            # Backtrack changes to assignment and domains
            assignment = assignment_copy
            self.domains = domain_copy
        return None

    
    def inference(self, var, assignment):
        """
        Draw inference from assignment of variable x. Returns False if assignment
        to variable x cannot maintain arc consistency, otherwise True.
        """

        
        arcs = []
        # Iterate through neighbors of the variable
        for neighbor in self.crossword.neighbors(var):
            # As long as the neighbor has not been assigned with a value
            if neighbor not in assignment:
                # Add the the arc to arcs list to check for arc consistency
                arcs.append((neighbor, var))

        arc_consistent =  self.ac3(arcs)
        # If they are arc consistent, 
        if arc_consistent:
            # Loop through domain of each variable
            for variable in self.domains:
                # If there is only one possible value in the domain
                if len(self.domains[variable]) == 1:
                    # Get that value
                    value = list(self.domains[variable])[0]
                    # Check if that value has already been assigned
                    if value not in assignment.values():
                        # If not then assign it to the current variable and return true
                        assignment[variable] = value
            return True
        return False



def main():

    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()
