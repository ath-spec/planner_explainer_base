(define (problem sussman)
    (:domain blocks)
    (:objects
        a b c d - block
        
        ;;added
        red yellow - colour
    )
    (:init
        (on d c)
        (clear d)
        (ontable a)
        (ontable b)
        (ontable c)
        (clear b)
        (clear a)
        (handempty)
        
        ;;added
        (colour-of a yellow)
        (colour-of b red)
        (colour-of c red)
        (colour-of d yellow)
        
        (handclean)
    
    )
    (:goal (and
    
    (on c d)
    (on b c)
    (on a b)
    ))
)
