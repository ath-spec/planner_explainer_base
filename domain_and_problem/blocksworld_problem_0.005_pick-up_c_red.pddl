(define (problem sussman_progressed)
(:domain blocks)
(:objects
a - block
b - block
c - block
d - block
red - colour
yellow - colour
)

(:init
(clear d)
(colour-of d yellow)
(colour-of b red)
(ontable b)
(colour-of a yellow)
(colour-of c red)
(clear a)
(holding c)
(on a b)
(last-colour red)
(ontable d)
)

(:goal
(and  (on c d) (on b c) (on a b))))
