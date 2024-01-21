from pyteal import *
import random

def approval_program():
    
    cibil = Btoi(Txn.application_args[1])

    approve = Seq(
          [
                App.globalPut(Bytes("approval"), Btoi(Bytes("Yes")))
          ]
    )

    deny = App.globalPut(Bytes("approval"), Btoi(Bytes("No")))

    card = Seq([
            If(
                Gt(cibil , Int(650)),
                approve,
                deny,
        ),
        Int(1)]
    )

    program = Cond(
        [Txn.application_id() == Int(0), Int(1)],
        [Txn.application_args[0] == Bytes("card"), card]
    )
    return program

# Clear program
def clear_program():
    return Int(1)

with open("approval_program.teal", "w") as f:
        compiled = compileTeal(approval_program(), mode=Mode.Application, version=4)
        f.write(compiled)

with open("clear_program.teal", "w") as f:
        compiled = compileTeal(clear_program(), mode=Mode.Application, version=4)
        f.write(compiled)

