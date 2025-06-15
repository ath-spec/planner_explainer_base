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
(handempty)
(colour-of d yellow)
(colour-of b red)
(last-colour yellow)
(colour-of a yellow)
(colour-of c red)
(clear a)
(on c d)
(on b c)
(on a b)
(ontable d)
)

(:goal
(and  (on c d) (on b c) (on a b))))
