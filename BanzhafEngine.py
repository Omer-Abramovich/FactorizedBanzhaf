from functools import reduce
# from graphviz import Digraph

class Value:
    """ stores a single dnf variable and its gradient"""

    def __init__(self, prob, vars = set(), _children=(), _op='', label = ''):
        self.prob = prob
        self.vars = vars
        self.grad = 0
        # internal variables used for autograd graph construction
        self._backward = lambda: None
        self._prev = set(_children)
        self._op = _op # the op that produced this node, for graphviz / debugging / etc
        self.label = str(label) #for printing purposes

    def __add__(self, other):
      other = other if isinstance(other, Value) else Value(other)
      out = Value(
            1 - (1-self.prob)*(1 - other.prob),
             self.vars.union(other.vars),
            (self, other), "V"
        )

      def _backward():
          self.grad += (1 - other.prob) * out.grad
          other.grad += (1 - self.prob) * out.grad
      out._backward = _backward

      return out

    @staticmethod
    def N_add(values):
      values = [(v if isinstance(v, Value) else Value(v)) for v in values]
      out = Value(
            1 - reduce(lambda x, y: x*(1 - y.prob), values, Value(1)).prob,
             set.union(*[v.vars for v in values]),
            set(values), "V"
        )

      def _backward():
          one_minus_prob_out = 1 - out.prob
          for v in values:
            v.grad += (one_minus_prob_out/(1 - v.prob)) * out.grad


      out._backward = _backward

      return out

    def __mul__(self, other):
        other = other if isinstance(other, Value) else Value(other)
        out = Value(self.prob * other.prob, self.vars.union(other.vars), (self, other), '^')

        def _backward():
            self.grad += other.prob * out.grad
            other.grad += self.prob * out.grad
        out._backward = _backward

        return out

    @staticmethod
    def N_mul(values):
      values = [(v if isinstance(v, Value) else Value(v)) for v in values]
      out = Value(
            reduce(lambda x, y: x*y.prob, values, Value(1)).prob,
             set.union(*[v.vars for v in values]),
            set(values), "*"
        )

      def _backward():
          for v in values:
            v.grad += (out.prob/v.prob) * out.grad

      out._backward = _backward

      return out

    def exc_or(self, other, ex_var):
        other = other if isinstance(other, Value) else Value(other)
        ex_var = ex_var if isinstance(ex_var, Value) else Value(ex_var)

        out = Value(self.prob * ex_var.prob + other.prob * (1- ex_var.prob), self.vars.union(other.vars).union(ex_var.vars), (self, other, ex_var), 'X' + ex_var.label)

        def _backward():
            self.grad += out.grad * ex_var.prob
            other.grad += out.grad * (1- ex_var.prob)
            ex_var.grad += out.grad * (self.prob - other.prob)
        out._backward = _backward

        return out

    def backward(self):

        # topological order all of the children in the graph
        topo = []
        visited = set()
        def build_topo(v):
            if v not in visited:
                visited.add(v)
                for child in v._prev:
                    build_topo(child)
                topo.append(v)
        build_topo(self)

        # go one variable at a time and apply the chain rule to get its gradient
        self.grad = 2**len(self.vars) if len(self.vars) < 100 else 1
        for v in reversed(topo):
            v._backward()

    def __neg__(self): # -self
        return self * -1

    def __radd__(self, other): # other + self
        return self + other

    def __sub__(self, other): # self - other
        return self + (-other)

    def __rsub__(self, other): # other - self
        return other + (-self)

    def __rmul__(self, other): # other * self
        return self * other

    def __truediv__(self, other): # self / other
        return self * other**-1

    def __rtruediv__(self, other): # other / self
        return other * self**-1

    def __repr__(self):
        # return f"{self.label}"
        return f"Value(label={self.label}, prob={self.prob}, grad={self.grad})"