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
(holding a)
(clear b)
(colour-of d yellow)
(colour-of b red)
(colour-of a yellow)
(ontable d)
(done_action_unstack-same-colour a b yellow)
(ontable b)
(last-colour yellow)
(colour-of c red)
(clear c)
(on c d)
)

(:goal
(and  (on c d) (on b c) (on a b))))
