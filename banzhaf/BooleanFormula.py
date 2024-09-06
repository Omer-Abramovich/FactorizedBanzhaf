from enum import Enum, auto

class Operator(Enum):
    AND = auto()
    OR = auto()

class BooleanFormula:
    def __init__(self, variable=None, op=None, subformulas=None, parent=None):
        if variable is not None:
            self.is_leaf = True
            self.variables = {variable}
            self.op = None
            self.subformulas = set()
            self.identity = variable
        elif subformulas is not None:
            self.is_leaf = False
            self.variables = set()
            for subformula in subformulas:
                subformula.parent = self
                if not isinstance(subformula, BooleanFormula):
                    raise ValueError("All subformulas must be instances of BooleanFormula")
                self.variables.update(subformula.variables) 
            
            if isinstance(op, Operator):
                self.op = op
            else:
                raise ValueError("Operator must be an instance of Operator enum")
            self.subformulas = set(subformulas)
        else:
            raise ValueError("Either variable or subformulas must be provided")
        
        self.parent = parent

    def partially_evaluate(self, variable, value):
        if self.is_leaf and self.identity == variable:
            self.value = value
            self.variables = set() #TODO Is necessary
            return True
        
        if variable not in self.variables:
            return False
        
        self.variables = set()
        if (self.op == Operator.OR and value) or (self.op == Operator.AND and not value):
            should_clear = False
            for subformula in self.subformulas:
                if subformula.partially_evaluate(variable, value):
                    should_clear = True
                    break 
                else:
                    self.variables.update(subformula.variables)

        else:
            should_clear = True
            to_remove = set()
            for subformula in self.subformulas:
                if subformula.partially_evaluate(variable, value):
                    to_remove.add(subformula)
                    # self.subformulas.remove(subformula)
                else:
                    should_clear = False
                    self.variables.update(subformula.variables)

            self.subformulas.difference_update(to_remove)
        if should_clear:
            self.variables = set()
            self.subformulas.clear()
            self.value = value
            return True
        else:
            return False        
            
    def __zero_variables__(self):
        for k in self.variables:
            self.variables[k] = 0

    def __count_variables__(self):
        self.__zero_variables__()
        for k in self.variables:
            self.variables[k]= sum(subformula.variables[k] for subformula in self.subformulas)

    def is_read_once(self):
        return all(v <= 1 for v in  self.variables.values())
    
    def get_max_variable(self):
        return max(self.variables, key=lambda x: self.variables[x])
   
        
    def __repr__(self):
        if not self.variables:
            return str(self.value)
        if self.op is None:
            return f"{list(self.variables)[0]}"  # Return the single variable
        else:
            subformulas_repr = f" {self.op.name} ".join(repr(subformula) for subformula in self.subformulas)
            return f"({subformulas_repr})"
        
def parse_formula(data, var_map=None, next_id=0):
    if var_map is None:
        var_map = {}

    if isinstance(data, str):
        if data not in var_map:
            # var_map[data] = Value(0.5, {next_id}, label=next_id)
            var_map[data] = next_id
            next_id += 1
        return BooleanFormula(variable=var_map[data]), var_map, next_id

    
    operator_map = {
        'and': Operator.AND,
        'or': Operator.OR
    }
    
    op = operator_map.get(data['operator'])
    subformulas = []
    for sub in data['subformula']:
        subformula, var_map, next_id = parse_formula(sub, var_map, next_id)
        subformulas.append(subformula)
    
    return BooleanFormula(op=op, subformulas=subformulas), var_map, next_id