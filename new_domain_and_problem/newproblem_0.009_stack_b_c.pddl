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
(clear b)
(colour-of d yellow)
(colour-of b red)
(colour-of a yellow)
(ontable d)
(done_action_unstack-same-colour a b yellow)
(clear a)
(colour-of c red)
(ontable a)
(on c d)
(on b c)
(last-colour red)
(handempty)
)

(:goal
(and  (on c d) (on b c) (on a b))))
