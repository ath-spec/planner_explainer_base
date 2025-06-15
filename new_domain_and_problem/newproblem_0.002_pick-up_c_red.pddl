(define (problem sussman_progressed_progressed_progressed)
(:domain newblocks)
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
(colour-of a yellow)
(ontable d)
(done_action_unstack-same-colour a b yellow)
(clear a)
(ontable b)
(colour-of c red)
(holding c)
(last-colour red)
(on a b)
)

(:goal
(and  (on c d) (on b c) (on a b))))
