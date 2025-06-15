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
(ontable a)
(colour-of d yellow)
(colour-of b red)
(colour-of a yellow)
(colour-of c red)
(clear a)
(on c d)
(holding b)
(clear c)
(last-colour red)
(ontable d)
)

(:goal
(and  (on c d) (on b c) (on a b))))
