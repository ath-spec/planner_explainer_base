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
(ontable a)
(colour-of d yellow)
(clear b)
(colour-of b red)
(handclean)
(colour-of a yellow)
(colour-of c red)
(clear a)
(on c d)
(on b c)
(ontable d)
)

(:goal
(and  (on c d) (on b c) (on a b))))
