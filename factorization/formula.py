class formula:
    def __init__(self, lineage):
        if type(lineage) is dict:
            self.operator = lineage["operator"]
            self.subformula = lineage["subformula"]
        else:
            self.operator = None
            self.subformula = lineage
        for index, element in enumerate(self.subformula):
            if type(element) != str and type(element) != formula:
                subformula = formula(element)
                self.subformula[index] = subformula
        
        self.variables_dict = self.get_variable_dict(self.subformula)
        self.variables = self.get_variables(self.subformula)
        self.variable_count = len(self.variables)

    def __str__(self):
        string = "{\"operator\": " + str(self.operator) +"," + "\n \"subformula\": ["
        list_of_strings = []
        for element in self.subformula:
            list_of_strings.append(str(element))
        return string + ", ".join(list_of_strings) +"]}"

    def get_variable_dict(self, subformula):
        variables_dict = {}
        for element in subformula:
            if isinstance(element, formula):
                for key, value in element.variables_dict.items():
                    if key in variables_dict:
                        variables_dict[key] += value
                    else:
                        variables_dict[key] = value
            elif isinstance(element, str):
                if element in variables_dict:
                    variables_dict[element] += 1
                else:
                    variables_dict[element] = 1
        return variables_dict

    def get_variables(self, subformula):
        variables = set()
        for element in subformula:
            if isinstance(element, formula):
                variables.update(element.variables)
            elif isinstance(element, str):
                variables.add(element)
        return variables
    
    def __try_to_find_independent_set(self):
        lineage = self.subformula.copy()
        clause_list_left, clause_list_right = [], []
        left_side_variables = set()
        right_side_variables = set()
        single_variables = []

        for element in lineage:
            if type(element) == str:
                single_variables.append(element)
        
        for element in lineage:
            if type(element) != str:
                if len(left_side_variables) == 0:
                    left_side_variables.update(element.variables)
                    clause_list_left.append(element)
                    continue
                if not set(element.variables).isdisjoint(left_side_variables):
                    clause_list_left.append(element)
                    left_side_variables.update(element.variables)
                else:
                    clause_list_right.append(element)
                    right_side_variables.update(element.variables)

        for variable in single_variables:
            checkSum = 0
            if variable in left_side_variables:
                clause_list_left.append(variable)
                checkSum += 1
            if variable in right_side_variables:
                clause_list_right.append(variable)
                checkSum += 1
            if checkSum == 0:
                clause_list_right.append(variable)
            if checkSum == 2:
                return False, None, None
    
        if len(clause_list_left) == 0 or len(clause_list_right) == 0 or not left_side_variables.isdisjoint(right_side_variables):
            return False, None, None

        if len(clause_list_left) == 1:
            left_formula = clause_list_left[0]
        else:
            left_formula = formula({"operator": self.operator , "subformula": clause_list_left})

        if len(clause_list_right) == 1:
            right_formula = clause_list_right[0]
        else:
            right_formula = formula({"operator": self.operator , "subformula": clause_list_right})

        left_formula = self.reduce_depth(left_formula)
        right_formula = self.reduce_depth(right_formula)

        return True, left_formula, right_formula 
  
    def try_to_find_independent_or(self):
        if self.operator != "or":
            return False, None, None
        return self.__try_to_find_independent_set()
        
    def try_to_find_independent_and(self):
        if self.operator != "and":
            return False, None, None
        return self.__try_to_find_independent_set()
    
    def set_variable_to_true(self, variable_to_remove):
        lineage = self.subformula.copy()

        #first run over all elements and only check variables not subformulas
        for index, element in enumerate(lineage):
            if isinstance(element, str):
                if element == variable_to_remove:
                    if self.operator == "and":
                        lineage.remove(element)
                        if len(lineage) == 0:
                            return True
                    elif self.operator == "or":
                        return True
            
        #only now run over all elements and only check subformulas
        for index, element in enumerate(lineage):
            if isinstance(element, formula) and variable_to_remove in element.variables:
                result = element.set_variable_to_true(variable_to_remove)
                if result == True:
                    lineage.remove(element)
                    if len(lineage) == 0:
                        return True
                else:
                    lineage[index] = result
             
        return formula({"operator": self.operator , "subformula": lineage})

    def set_variable_to_false(self, variable_to_remove):
        lineage = self.subformula.copy()

        #first run over all elements and only check variables not subformulas
        for index, element in enumerate(lineage):
            if isinstance(element, str):
                if element == variable_to_remove:
                    if self.operator == "and":
                        return False
                    elif self.operator == "or":
                        lineage.remove(element)
                        if len(lineage) == 0:
                            return False

        #only now run over all elements and only check subformulas
        for index, element in enumerate(lineage):
            if isinstance(element, formula) and variable_to_remove in element.variables:
                result = element.set_variable_to_false(variable_to_remove)
                if result == False:
                    lineage.remove(element)
                    if len(lineage) == 0:
                        return False
                else:
                    lineage[index] = result
             
        return formula({"operator": self.operator , "subformula": lineage})

    def reduce_depth(self, formula):
        return formula
        parentOperator = self.operator

        if isinstance(formula, str):
            return formula
        if isinstance(formula, bool):
            return formula
            
        for index, clause in enumerate(formula.subformula):
            try:
                if clause.operator == parentOperator:
                    formula.subformula.pop(index)
                    formula.subformula += clause.subformula
                    formula.reduce_depth(formula.subformula)
                else:
                    formula.subformula[index] = formula.reduce_depth(clause)  

            except:
                continue

        if len(formula.subformula) == 1:
            return formula.subformula[0]

        return formula

    def find_exclusive_or(self):
        variable_to_remove = max(self.variables_dict, key=lambda key: self.variables_dict[key])
        
        left_formula = self.set_variable_to_true(variable_to_remove)
        right_formula = self.set_variable_to_false(variable_to_remove)

        left_formula = self.reduce_depth(left_formula)
        right_formula = self.reduce_depth(right_formula)
               
        return left_formula, right_formula, variable_to_remove
    
    def satisfying_assignments(self):
        if self.operator == "and":
            result = 1
        
        if self.operator == "or":
            result = 2 ** (self.variable_count) -1

        return result
    
    def satisfying_assignments_fact(self, fact):
        if fact not in self.variables:
            return 0
        
        if self.operator == "and":
            result = 1
        
        if self.operator == "or":
            result = 2 ** (self.variable_count) -1

        return result
    
    def satisfying_assignments_without_fact(self, fact):
        if fact not in self.variables:
            if self.operator == "and":
                return 1
            if self.operator == "or":
                return 2 ** (self.variable_count) -1
        else:
            if self.operator == "and":
                return 0
            if self.operator == "or":
                return 2 ** (self.variable_count) -2 #minus one when all are false and minus one when only would be true
        
        return 0

    def critical_assignments_for_fact(self, fact):
        if fact not in self.variables:
            return 0

        satisfied_assignment_with_fact = self.satisfying_assignments_fact(fact)
        satisfied_assignment_without_fact = self.satisfying_assignments_without_fact(fact)

        return satisfied_assignment_with_fact - satisfied_assignment_without_fact