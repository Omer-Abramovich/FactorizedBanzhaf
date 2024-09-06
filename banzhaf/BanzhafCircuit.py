from collections import defaultdict
from .BanzhafEngine import Value
import time

class DNFCircuit():
  timeout = 0

  def __init__(self, dnf, timeout = 3600):
        DNFCircuit.timeout = timeout
        tmp_vars = set(item for clause in dnf for item in clause)
        var_to_val = {v: Value(0.5, {v}, label=v) for v in tmp_vars}
        self.var_dict = var_to_val
        self.vars = list(var_to_val.values())
        self.dnf = lift_recursively([set([var_to_val[v] for v in clause]) for clause in dnf])
        # print(len(self.dnf))
        self.root = self.build_dtree()

  def build_dtree(self):
    DNFCircuitNode.start_time = time.time()
    root = DNFCircuitNode(self.dnf, "root")
    root.recursively_expand()
    root.value.backward()
    self.banzhaf_values = [(v.label, v.grad * v.prob) for v in self.vars]
    return root
  


class DNFCircuitNode():
  start_time = 0

  def __init__(self, dnf, op = "leaf", children=set(), parent=None):
        if time.time() - DNFCircuitNode.start_time > DNFCircuit.timeout:
           print(time.time(), DNFCircuitNode.start_time, DNFCircuit.timeout)
           raise TimeoutError("timeout exceeded")
        
        self.dnf = dnf
        self.op = op
        self.children = children
        self.parent = parent
        self.value = None

  def perform_op(self):
    if self.op == "+":
      self.value = Value.N_add([child.value for child in self.children])
    elif self.op == "*":
      self.value = Value.N_mul([child.value for child in self.children])
    elif isinstance(self.op, Value):
      self.value = self.children[0].value.exc_or(self.children[1].value, self.op)
    else:
      assert False

  def recursively_expand(self):
    expansion_res = expand(self.dnf)
    if not expansion_res[0]:
      self.value = Value.N_mul(self.dnf[0])
    else:
      self.children = [DNFCircuitNode(child) for child in expansion_res[1]]
      self.op = expansion_res[2]
      for child in self.children:
        if set() in child.dnf:
          print(self.op)
          print(self.dnf)
          print(child.dnf)
        child.recursively_expand()
      self.perform_op()


def ind_or(dnf):
    uf = UnionFind()
    for clause in dnf:
        x = set_first(clause)
        for idx, fact in enumerate(clause):
            if idx > 0:
              uf.union(fact, x)

    outputs = dict()
    for idx, clause in enumerate(dnf):
        k = uf.find(set_first(clause))
        if k in outputs:
            outputs[k].append(clause)
        else:
            outputs[k] = [clause]

    if len(outputs) > 1:
      return True, list(outputs.values())
    else:
      return False, []

def ind_and(dnf):
  candidates = set(dnf[0])
  for i in range(1, len(dnf)):
    candidates = candidates.intersection(dnf[i])
    if len(candidates) == 0:
      break
  if len(candidates) == 0:
    return False, []
  else:
    dnf = [clause - candidates for clause in dnf]
    return True, [[candidates], dnf]

def exc_or(dnf):
  dnf = [clause.copy() for clause in dnf]
  counts = defaultdict(int)

  for clause in dnf:
    for fact in clause:
        counts[fact] += 1
  max_fact = max(counts, key=counts.get)

  false_dnf = []
  tmp_dnf = []
  for clause in dnf:
    if max_fact not in clause:
      false_dnf.append(clause)
    else:
      tmp_dnf.append(clause - {max_fact})

  tmp_dnf = tmp_dnf + false_dnf
  tmp_dnf.sort(key=len)
  true_dnf = []

  for clause in tmp_dnf:
    if not any(existing_set.issubset(clause) for existing_set in true_dnf):
      true_dnf.append(clause)

  return max_fact, [true_dnf, false_dnf]

def lift_recursively(dnf):
  success = True
  while success and len(dnf) > 1:
    success, dnf = lift(dnf)
  return dnf

def lift(dnf):
  neighbors = defaultdict(set) #holding neighbors for each fact
  candidates = dict() #holding possible candidates for conjucntion for each fact
  for clause in dnf:
    for fact in clause:
      adjusted_clause = clause - {fact}
      neighbors[fact].add(frozenset(adjusted_clause))
      if fact in candidates:
        candidates[fact] &= adjusted_clause
      else:
        candidates[fact] = adjusted_clause

  lifted_dict_disjunction = defaultdict(list)
  for key, val in neighbors.items():
    lifted_dict_disjunction[frozenset(val)].append(key)

  lifted_dict_disjunction = list(filter(lambda x: len(x) > 1, lifted_dict_disjunction.values()))

  lifted_dict_conjuction = defaultdict(list)
  for key, val in candidates.items():
    for v in val:
      if v not in lifted_dict_conjuction and key in candidates[v]:
        lifted_dict_conjuction[key].append(v)

  lifted_dict_conjuction = [[k] + v for k,v in lifted_dict_conjuction.items()]

  #TODO - merge with similar code above
  replace = dict()
  delete = set()
  for group in lifted_dict_disjunction:
    new_val = Value.N_add(group)
    new_val.label = f"+{len(group)}" # for visualization, consider removing (TODO)
    replace[group[0]] = new_val
    delete |= set(group[i] for i in range(1, len(group)))

  new_dnf = []
  for clause in dnf:
    if all(fact not in delete for fact in clause):
      new_clause = {replace[fact] if fact in replace else fact for fact in clause}
      new_dnf.append(new_clause)

  replace = dict()
  delete = set()
  for group in lifted_dict_conjuction:
    new_val = Value.N_mul(group)
    new_val.label = f"*{len(group)}" # for visualization, consider removing (TODO)
    replace[group[0]] = new_val
    delete |= set(group[i] for i in range(1, len(group)))

  newer_dnf = []
  for clause in new_dnf:
    if any(fact in replace for fact in clause):
      new_clause = {replace[fact] if fact in replace else fact for fact in clause if fact not in delete}
      newer_dnf.append(new_clause)
    else:
      newer_dnf.append(clause)

  return bool(lifted_dict_disjunction or lifted_dict_conjuction), newer_dnf

def expand(dnf):
  if len(dnf) == 1:
    return False, []

  res = ind_or(dnf)
  op = "+"
  children = res[1]
  if not res[0]:
    res = ind_and(dnf)
    op = "*"
    children = res[1]
  if not res[0]:
    res = exc_or(dnf)
    op = res[0]
    children = [lift_recursively(child) for child in res[1]]


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
  
# Takes DNF of form list of lists with arbitrary datatype, and converts it into DNF of form list of sets of integer datatype.  
def convert_dnf(dnf):
  numbered_mapping = dict()
  vars = set()
  for clause in dnf:
      vars.update(clause)
  for idx, var in enumerate(vars):
      numbered_mapping[var] = idx
  res = [set([numbered_mapping[fact] for fact in clause]) for clause in dnf]
  return res, numbered_mapping