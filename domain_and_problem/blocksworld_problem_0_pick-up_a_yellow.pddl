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
(ontable c)
(holding a)
(colour-of d yellow)
(clear b)
(colour-of b red)
(last-colour yellow)
(ontable b)
(colour-of a yellow)
(on d c)
(colour-of c red)
)

(:goal
(and  (on c d) (on b c) (on a b))))
