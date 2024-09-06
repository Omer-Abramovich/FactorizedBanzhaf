import time
from BanzhafEngine import Value
from copy import deepcopy
from collections import defaultdict
from BooleanFormula import *


class BooleanCircuit():
  var_to_val = dict()
  timeout = 0
  dtype = None

  def __init__(self, formula, timeout = 200, dtype = int):
        BooleanCircuit.timeout = timeout
        BooleanCircuit.var_to_val = dict()
        BooleanCircuit.dtype = dtype
        self.formula = formula
        self.vars = formula.variables
        for var in self.vars:
           BooleanCircuit.var_to_val[var] = Value(prob=0.5, vars={var}, label=var)
        self.root = self.build_dtree()

  def build_dtree(self):
    BooleanCircuitNode.start_time = time.time()
    root = BooleanCircuitNode(self.formula, "root")
    root.recursively_expand()
    root.value.vars.difference_update({'TRUE', 'FALSE'})

    root.value.backward()
    # self.banzhaf_values = [(v.label, v.grad * v.prob) for v in self.vars]
    self.banzhaf_values = [(v.label, v.grad * v.prob) for v in BooleanCircuit.var_to_val.values()]
    return root
  
TRUE_FORMULA = BooleanFormula(Value(1, vars={"TRUE"}, label="TRUE"))
FALSE_FORMULA = BooleanFormula(Value(0, vars={"FALSE"}, label="FALSE"))

class BooleanCircuitNode():
  start_time = 0

  def __init__(self, formula, op = "leaf", children=set(), parent=None):
        if time.time() - BooleanCircuitNode.start_time > BooleanCircuit.timeout:
           print(time.time(), BooleanCircuitNode.start_time, BooleanCircuit.timeout)
           assert False
        self.formula = formula
        self.op = op
        self.children = children
        self.parent = parent
        self.value = None

  def perform_op(self):
    if self.op == "+":
      self.value = Value.N_add([child.value for child in self.children])
    elif self.op == "*":
      self.value = Value.N_mul([child.value for child in self.children])
    elif isinstance(self.op, BooleanCircuit.dtype):
      self.value = self.children[0].value.exc_or(self.children[1].value, BooleanCircuit.var_to_val[self.op])
    else:
      assert False

  def recursively_expand(self):
    success, children, op = expand(self.formula)

    if not success:
    #   self.value = Value.N_mul(self.formula[0]) #TODO change to formula.variable????
        # self.value = self.formula.identity #TODO change to formula.variable????
        relevant_var = set_first(self.formula.variables) if self.formula.variables else self.formula.identity
        self.value = BooleanCircuit.var_to_val[relevant_var] if relevant_var in BooleanCircuit.var_to_val else relevant_var #TODO change to formula.variable????


    else:
      self.children = [BooleanCircuitNode(child) for child in children]
      self.op = op
      for child in self.children:
        child.recursively_expand()
      self.perform_op()

def ind_separation(formula):
    uf = UnionFind()
    for subformula in formula.subformulas:
        x = set_first(subformula.variables)
        for idx, fact in enumerate(subformula.variables):
            if idx > 0:
              uf.union(fact, x)

    outputs = dict()
    for idx, subformula in enumerate(formula.subformulas):
        k = uf.find(set_first(subformula.variables))
        if k in outputs:
            outputs[k].append(subformula)
        else:
            outputs[k] = [subformula]

    if len(outputs) > 1:
      return True, [BooleanFormula(op = formula.op, subformulas=f) if len(f) > 1 else f[0] for f in outputs.values()]
    else:
      return False, []
   
def count_variables(formula):
    counts = defaultdict(int)
    for subformula in formula.subformulas:
        for variable in subformula.variables:
            counts[variable] += 1
    return counts

def exc_or(formula):
  formula_true = deepcopy(formula)
  formula_false = deepcopy(formula) #TODO maybe we don't need a second copy

  counts = count_variables(formula) #TODO 
  max_fact = max(counts, key=counts.get) # TODO

  if formula_true.partially_evaluate(max_fact, True):
     formula_true = TRUE_FORMULA
  if formula_false.partially_evaluate(max_fact, False):
     formula_false = FALSE_FORMULA

  return max_fact, [formula_true, formula_false]

def expand(formula):
  if formula.is_leaf or not formula.variables:
    return False, [], None
  elif len(formula.variables) == 1:
    #  formula.identity = BooleanCircuit.var_to_val[set_first(formula.variables)]
     return False, [], None

  res, children = ind_separation(formula)
  if res:
     op = "+" if formula.op == Operator.OR else "*"
  else:
    op, children = exc_or(formula)
    # children = [lift_recursively(child) for child in res[1]] #TODO, consider lifting


  return True, children, op


class KeyDefaultDict(dict):
    def __missing__(self, key):
      return key

class UnionFind:
    def __init__(self):
        self.parent = KeyDefaultDict()

    def find(self, x):
        if self.parent[x] is None:
            return None
        path = []
        while x != self.parent[x]:
            path.append(x)
            x = self.parent[x]
        for node in path:
            self.parent[node] = x
        return x

    def union(self, x, y):
        x_root = self.find(x)
        y_root = self.find(y)
        if x_root is not None and y_root is not None and x_root != y_root:
            self.parent[x_root] = y_root


def set_first(s):
  for e in s:
    return e