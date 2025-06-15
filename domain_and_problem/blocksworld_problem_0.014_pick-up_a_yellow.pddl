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
(holding a)
(colour-of d yellow)
(clear b)
(colour-of b red)
(last-colour yellow)
(colour-of a yellow)
(colour-of c red)
(on c d)
(on b c)
(ontable d)
)

(:goal
(and  (on c d) (on b c) (on a b))))
