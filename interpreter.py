import os
import sys
import time
from enum import Enum, IntEnum
from compiler import compileFile

class FileReader():
    def __init__(self, fname):
        self.Line = 0
        self.FName = fname
        self.File = open(fname)
            
    def getLine(self):
        self.Line += 1
        return self.File.readline()
    
    def getLineNo(self):
        return self.Line

    def getFName(self):
        return self.FName

compileFile("{0}".format(sys.argv[1]))
fileReaders = [FileReader("{0}.asop".format(sys.argv[1]))]

class StackObjectType(Enum):
    VARIABLE        = 1
    INTEGER         = 2
    FLOAT           = 3
    STRING          = 4
    PARENTHESIS     = 5
    BOOLEAN         = 6
    CONTROL         = 7
    
variables   = {}
labels      = {} # Stores the line no. of labels

class StackObject():
    def __init__(self, objectType, value, identifier = -1):
        self.ObjectType = objectType
        self.Value = value
        if objectType == StackObjectType.VARIABLE:
            if not value in variables:
                variables[value] = 0
                
    def getType(self):
        return self.ObjectType
    
    def getValue(self):
        global variables
        if self.ObjectType == StackObjectType.VARIABLE:
            return variables[self.Value]
        else:
            return self.Value

    def getBooleanValue(self):
        if self.getType() == StackObjectType.BOOLEAN:
            return self.getValue()
        elif self.getType() == StackObjectType.INTEGER:
            return True if self.getValue() != 0 else False

    def getIdentifier(self):
        return self.Value

    def add(self, s2):
        if self.getType() == StackObjectType.INTEGER:
            if s2.getType() == StackObjectType.INTEGER or s2.getType() == StackObjectType.VARIABLE:
                return StackObject(StackObjectType.INTEGER, self.getValue() + s2.getValue())
            elif s2.getType() == StackObjectType.STRING:
                return StackObject(StackObjectType.STRING, str(self.getValue()) + s2.getValue())
            elif s2.getType() == StackObjectType.FLOAT:
                return StackObject(StackObjectType.FLOAT, self.getValue() + s2.getValue())
        elif self.getType() == StackObjectType.FLOAT:
            if s2.getType() == StackObjectType.INTEGER or s2.getType() == StackObjectType.VARIABLE or s2.getType() == StackObjectType.FLOAT:
                return StackObject(StackObjectType.FLOAT, self.getValue() + s2.getValue())
            elif s2.getType() == StackObjectType.STRING:
                return StackObject(StackObjectType.STRING, str(self.getValue()) + s2.getValue())
        elif self.getType() == StackObjectType.STRING:
            return StackObject(StackObjectType.STRING, self.getValue() + str(s2.getValue()))
        elif self.getType() == StackObjectType.VARIABLE:
            if s2.getType() == StackObjectType.STRING:
                return StackObject(StackObjectType.STRING, str(self.getValue()) + s2.getValue())
            elif s2.getType() == StackObjectType.INTEGER:
                return StackObject(StackObjectType.INTEGER, self.getValue() + s2.getValue())
            
    def subtract(self, s2):
        pass
    
    def divide(self, s2):
        if self.getType() == StackObjectType.INTEGER or self.getType() == StackObjectType.FLOAT:
            if s2.getType() == StackObjectType.INTEGER or self.getType() == StackObjectType.FLOAT or s2.getType() == StackObjectType.VARIABLE:
                return StackObject(StackObjectType.FLOAT, self.getValue() / s2.getValue())
            elif s2.getType() == StackObjectType.STRING:
                Error.major("Operator", "Number", "String")
                
    def multiply(self, s2):
        return StackObject(StackObjectType.INTEGER, self.getValue() * s2.getValue())

    def equals(self, s2):
        return StackObject(StackObjectType.BOOLEAN, self.getValue() == s2.getValue())

def setVariable(var, val):
    variables[var.getIdentifier()] = val.getValue()

def push(line):
    if line.startswith("I"):
        stack.append(StackObject(StackObjectType.INTEGER, int(line[2:])))
    elif line.startswith("F"):
        stack.append(StackObject(StackObjectType.FLOAT, float(line[2:])))
    elif line.startswith("V"):
        stack.append(StackObject(StackObjectType.VARIABLE, line[2:]))
    elif line.startswith("S"):
        stack.append(StackObject(StackObjectType.STRING, line[2:]))
    else:
        Error.major("Push error", "Type", "Nothing")

def call(fn, args):
    if fn.getIdentifier() == "import":
        filen = args[0].getValue()
        if os.path.exists("{0}.AScript".format(filen)):
            print("\n\n><_> RUNTIME COMPILE - {0} <_><\n\n".format(filen))
            compileFile(filen)
        
        if os.path.exists("{0}.asop".format(filen)):
            fileReaders.append(FileReader("{0}.asop".format(filen)))
        else:
            stack.append(StackObject(StackObjectType.BOOLEAN, False))
    elif fn.getIdentifier() == "print":
        for argz in args:
            print(argz.getValue())
    elif fn.getIdentifier() == "input":
        if len(args) > 0:
            stack.append(StackObject(StackObjectType.STRING, input(args[0].getValue())))
        else:
            stack.append(StackObject(StackObjectType.STRING, input()))
    elif fn.getIdentifier() == "sqrt":
        if len(args) > 0 and args[0].getType() == StackObjectType.INTEGER or args[0].getType() == StackObjectType.FLOAT or args[0].getType() == StackObjectType.VARIABLE:
            stack.append(StackObject(StackObjectType.FLOAT, args[0].getValue() ** 0.5))
        else:
            Error.major("Sqrt Error", "INTEGER", " ")
    elif fn.getIdentifier() == "sleep":
        length = args[0].getValue()
        time.sleep(length)

def control(line):
    global labels
    
    if line.startswith("GOTOIFNOT"):
        # We should have a boolean at the top of the stack.
        b1 = stack.pop()
        
        if b1.getBooleanValue() == True:
            return
        else:
            gtnum = line[10:]
            goto(gtnum)
    elif line.startswith("GOTO"):
        gtnum = line[5:]
        goto(gtnum)
    elif line.startswith("LABEL"):
        lbl = line[6:]
        if lbl in labels:
            pass
        else:
            labels[lbl] = fileReaders[-1].getLineNo()

def goto(gotono):
    global labels

    if gotono in labels:
        fileN = gotono.split("?", 1)[0]
        fileReaders.pop()
        fileReaders.append(FileReader("{0}.asop".format(fileN)))
        for lineN in range(1, labels[gotono]): # labels[gotono] is lineno
            fileReaders[-1].getLine()
    else:
        line = fileReaders[-1].getLine()
        while not (line == "CNTRL LABEL {0}\n".format(gotono)):
            line = fileReaders[-1].getLine()

def op(line):
    if line == "+":
        i2 = stack.pop()
        i1 = stack.pop()
        stack.append(i1.add(i2))
    elif line == "-":
        i2 = stack.pop()
        i1 = stack.pop()
        stack.append(i1.subtract(i2))
    elif line == "*":
        i2 = stack.pop()
        i1 = stack.pop()
        stack.append(i1.multiply(i2))
    elif line == "/":
        i2 = stack.pop()
        i1 = stack.pop()
        stack.append(i1.divide(i2))
    elif line == "=":
        i2 = stack.pop()
        i1 = stack.pop()
        setVariable(i1, i2)
        stack.append(StackObject(StackObjectType.INTEGER, i2))
    elif line == "(":
        stack.append(StackObject(StackObjectType.PARENTHESIS, "("))
    elif line == ")":
        stack.append(StackObject(StackObjectType.PARENTHESIS, ")"))
    elif line == "==":
        i2 = stack.pop()
        i1 = stack.pop()
        stack.append(i1.equals(i2))
    else:
        Error.major("Invalid operator", "operator", "-{0}-".format(line))

class Error:
    ErrorCount = 0
    @staticmethod
    def major(val, exp, got):
        print("Error: {0} (At line {1})".format(val, fileReaders[-1].getLineNo()), "Expected: ", exp, " Got: ", got)
        Error.ErrorCount += 1

print(" /------------><------------\\")
print(" | INITIALIZING INTERPRETER |")
print(" \\------------><------------/")


line = fileReaders[-1].getLine()
stack = []
while line != "~EOF":
    if line.startswith("PUSH"):
        push(line[5:-1])
    elif line.startswith("OP"):
        op(line[3:-1])
    elif line.startswith("CALL"):
        arg = stack.pop()
        args = []
        if arg.getType() == StackObjectType.PARENTHESIS:
            arg = stack.pop()
            while arg.getType() != StackObjectType.PARENTHESIS and arg.getValue() != ")":
                args.append(arg)
                arg = stack.pop()
        else:
            args.append(arg)
        arg = stack.pop()
        args.reverse()
        call(arg, args)
    elif line.startswith("CNTRL"):
        control(line[6:-1])
    elif line.startswith("EOS"):
        pass
    else:
        Error.major("UNKNOWN TOKEN", "Parsable opcode", "UNKNOWN")
    
    line = fileReaders[-1].getLine()

    if line == "~EOF" and len(fileReaders) > 1:
        fileReaders.pop()
        line = fileReaders[-1].getLine()
