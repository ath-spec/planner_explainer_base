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
(ontable c)
(colour-of d yellow)
(colour-of b red)
(last-colour yellow)
(ontable b)
(colour-of a yellow)
(colour-of c red)
(clear a)
(holding d)
(clear c)
(on a b)
)

(:goal
(and  (on c d) (on b c) (on a b))))
