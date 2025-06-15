(define (domain newblocks)
  (:requirements :strips :typing)
  (:types block 
          ;added
          colour
  )
  (:predicates (on ?x - block ?y - block)
	       (ontable ?x - block)
	       (clear ?x - block)
	       (handempty)
	       (holding ?x - block)
	       
	       ;;added 
           (colour-of ?b - block ?c - colour)
	       (last-colour ?c - colour)
	       (handclean)
	       
    (done_action_unstack-same-colour ?x - block ?y - block ?c - colour)
	       )


   (:action clean
  :parameters(?c - colour)
  :precondition(and (handempty) (last-colour ?c))
  :effect(and 
  	(handclean) 
  	(not (last-colour ?c)))
   )	
	             
  (:action pick-up
	     :parameters (?x - block
                          ;added      
                          ?c - colour
	     )
	     :precondition (and (clear ?x) (ontable ?x) (handempty) 
                                ;;added
                                (colour-of ?x ?c)
                                (handclean)
	     )
	     :effect
	     (and (not (ontable ?x))
		   (not (clear ?x))
		   (not (handempty))
		   (holding ?x)
                   ;;added
                   (not (handclean))
                   (last-colour ?c)
            )
  )
  
  (:action pick-up-same-colour
	     :parameters (?x - block
                          ;added      
                          ?c - colour
	     )
	     :precondition (and (clear ?x) (ontable ?x) (handempty) 
                                ;;added
                                (colour-of ?x ?c)
                                (last-colour ?c)
	     )
	     :effect
	     (and (not (ontable ?x))
		   (not (clear ?x))
		   (not (handempty))
		   (holding ?x)
                   ;;added
                   (not (handclean))
                   (last-colour ?c)
            )
  )

  (:action put-down
	     :parameters (?x - block)
	     :precondition (holding ?x)
	     :effect
	     (and (not (holding ?x))
		   (clear ?x)
		   (handempty)
		   (ontable ?x)))
  (:action stack
	     :parameters (?x - block ?y - block)
	     :precondition (and (holding ?x) (clear ?y))
	     :effect
	     (and (not (holding ?x))
		   (not (clear ?y))
		   (clear ?x)
		   (handempty)
		   (on ?x ?y)))
  (:action unstack
	     :parameters (?x - block ?y - block ?c - colour)
	     :precondition (and (on ?x ?y) (clear ?x) (handempty)
                                ;;added
                                (colour-of ?x ?c)
                                (handclean)
	     
	     )
	     :effect
	     (and (holding ?x)
		   (clear ?y)
		   (not (clear ?x))
		   (not (handempty))
		   (not (on ?x ?y))
                   ;;added
                   (not (handclean))
                   (last-colour ?c)
            )
    )
    
    (:action unstack-same-colour
	     :parameters (?x - block ?y - block ?c - colour)
	     :precondition (and (on ?x ?y) (clear ?x) (handempty)
                                ;;added
                                (colour-of ?x ?c)
                                (last-colour ?c)    
	     
	     )
	     :effect
	     (and (holding ?x)
  (done_action_unstack-same-colour ?x ?y ?c)
		   (clear ?y)
		   (not (clear ?x))
		   (not (handempty))
		   (not (on ?x ?y))
                   ;;added
                   (not (handclean))
                   (last-colour ?c)
            )
		   
    ))