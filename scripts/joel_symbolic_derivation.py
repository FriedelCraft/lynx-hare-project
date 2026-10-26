"""Symbolic checks for Joel's section (needs sympy: pip install sympy): Rosenzweig-MacArthur equilibria, Jacobian, Hopf.

dH/dt = r H (1 - H/K) - a H P / (b + H)
dP/dt = e a H P / (b + H) - m P
"""
import sympy as sp

H, P, r, K, a, b, e, m = sp.symbols('H P r K a b e m', positive=True)
f = r*H*(1 - H/K) - a*H*P/(b + H)
g = e*a*H*P/(b + H) - m*P
J = sp.Matrix([f, g]).jacobian([H, P])
print("Jacobian:"); sp.pprint(sp.simplify(J))

# Equilibria
Hs = m*b/(e*a - m)
Ps = sp.simplify((r/a)*(1 - Hs/K)*(b + Hs))
assert sp.simplify(f.subs({H: Hs, P: Ps})) == 0
assert sp.simplify(g.subs({H: Hs, P: Ps})) == 0
print("H* =", Hs, "  P* =", sp.factor(Ps))

# E0, E1
print("J(E0) =", J.subs({H: 0, P: 0}))
print("J(E1) =", sp.simplify(J.subs({H: K, P: 0})))

# Coexistence: trace and determinant, using H* as a symbol h with P* from prey nullcline
h = sp.symbols('h', positive=True)
Ph = (r/a)*(1 - h/K)*(b + h)
Jh = J.subs({H: h, P: Ph})
# predator equation at equilibrium: e a h/(b+h) = m  ->  substitute e = m (b+h)/(a h)
Jh = sp.simplify(Jh.subs(e, m*(b + h)/(a*h)))
tr = sp.simplify(Jh.trace()); det = sp.simplify(Jh.det())
print("J(E*) =", Jh)
KH = b + 2*h
assert sp.simplify(tr - r*h*(K - KH)/(K*(b + h))) == 0
assert sp.simplify(det - r*m*b*(K - h)/(K*(b + h))) == 0
print("trace =", sp.factor(tr)); print("det   =", sp.factor(det))

# Hopf threshold in original parameters and transversality
KH_par = sp.simplify((b + 2*Hs))
assert sp.simplify(KH_par - b*(e*a + m)/(e*a - m)) == 0
dtr = sp.simplify(sp.diff(r*h*(K - KH)/(K*(b + h)), K).subs(K, KH))
print("K_H =", sp.factor(KH_par), "  d tr/dK at K_H =", sp.factor(dtr))
w0sq = sp.simplify(det.subs(K, KH))
print("omega0^2 at K_H =", sp.factor(w0sq))

# m-bands
print("predator persists iff m <", sp.simplify(e*a*K/(b + K)))
print("cycles iff m <", sp.solve(sp.Eq(b*(e*a + m)/(e*a - m), K), m))

# Prey nullcline hump
Pn = (r/a)*(1 - H/K)*(b + H)
Hpk = sp.solve(sp.diff(Pn, H), H)[0]
print("prey-nullcline peak at H =", Hpk, " height =", sp.factor(Pn.subs(H, Hpk)))

# Elasticities of K_H
for s in (b, m, a, e):
    el = sp.simplify(sp.diff(KH_par, s)*s/KH_par)
    print(f"elasticity of K_H wrt {s}:", sp.factor(el))
print("elasticity of H* wrt m:", sp.factor(sp.simplify(sp.diff(Hs, m)*m/Hs)))

# Scale invariance of predator units: P -> cP, a -> a/c, e -> e c
c = sp.symbols('c', positive=True)
Q = sp.symbols('Q', positive=True)
fq = (r*H*(1 - H/K) - (a/c)*H*Q/(b + H))
gq = (e*c)*(a/c)*H*Q/(b + H) - m*Q
assert sp.simplify(fq - f.subs(P, Q/c)) == 0
assert sp.simplify(gq - c*g.subs(P, Q/c)) == 0
print("Check: (a,e,P) -> (a/c, e c, cP) leaves dynamics invariant: OK")
