(define (problem sussman_progressed_progressed)
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
(ontable c)
(colour-of b red)
(colour-of a yellow)
(colour-of c red)
(ontable d)
(clear d)
(colour-of d yellow)
(last-colour yellow)
(holding a)
(done_action_unstack-same-colour a b yellow)
(clear c)
(ontable b)
)


(:goal (and
    
    (on c d)
    (on b c)
    (on a b)
    ))
)