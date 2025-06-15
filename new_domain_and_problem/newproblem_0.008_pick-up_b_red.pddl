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
(colour-of d yellow)
(colour-of b red)
(colour-of a yellow)
(ontable d)
(done_action_unstack-same-colour a b yellow)
(clear a)
(colour-of c red)
(clear c)
(ontable a)
(on c d)
(holding b)
(last-colour red)
)

(:goal
(and  (on c d) (on b c) (on a b))))
