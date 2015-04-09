from enum import Enum
import sys

lookahead       = -1

class FileReader():
    ThrowbackVar = -1
    LineNumber = 1

    @staticmethod
    def openFile(fname):
        FileReader.FileName = fname
        FileReader.File = open("{0}.AScript".format(fname))
        Emitter.File = open("{0}.asop".format(fname), 'w+')
    
    @staticmethod
    def getChar():
        if FileReader.ThrowbackVar != -1:
            lChar = FileReader.ThrowbackVar
            FileReader.ThrowbackVar = -1
            return lChar
        else:
            return FileReader.File.read(1)

    @staticmethod
    def returnChar(c):
        FileReader.ThrowbackVar = c

    @staticmethod
    def incrementLine():
        FileReader.LineNumber += 1

    @staticmethod
    def getLine():
        return FileReader.LineNumber

    @staticmethod
    def getFileName():
        return FileReader.FileName

class SymTable():
    Symbols = ["import"]

    @staticmethod
    def exists(identifier):
        if identifier in SymTable.Symbols:
            return SymTable.Symbols.index(identifier)
        else:
            return -1

    @staticmethod
    def insert(identifier):
        if not identifier in SymTable.Symbols:
            SymTable.Symbols.append(identifier)
            return len(SymTable.Symbols) - 1
        
    @staticmethod
    def getToken(identifier):
        identifierID = SymTable.exists(identifier)
        if identifierID != -1:
            return LexToken(TokenType.IDENTIFIER, identifier)
            #return LexToken(TokenType.IDENTIFIER, identifierID)
        else:
            SymTable.insert(identifier)
            return LexToken(TokenType.IDENTIFIER, identifier)
            #return LexToken(TokenType.IDENTIFIER, SymTable.insert(identifier))

    @staticmethod
    def getIdentifierName(index):
        return index
        #return SymTable.Symbols[index]

class TokenType(Enum):
    NUMBER          = 1
    IDENTIFIER      = 2
    OPERATION       = 3
    STRING          = 4
    SPECIAL         = 5
    ARRYLITERAL     = 6
    CALL            = 997
    EOS             = 998
    DONE            = 999

class LexToken():
    def __init__(self, tokenType, tokenValue, lexeme = ""):
        self.TokenType = tokenType
        self.TokenValue = tokenValue
        self.Lexeme = lexeme
    def getTokenType(self):
        return self.TokenType
    def getTokenValue(self):
        return self.TokenValue
    def getLexeme(self):
        return self.Lexeme

def begin(fname):
    FileReader.openFile(fname)
    parse()
    Emitter.save()

    print("\n\n /--------------------------------\\")
    print(" | COMPILE COMPLETE | ERRORS: {0}   |".format(Error.getErrorCount()))
    print(" \\--------------------------------/\n\n")

def lexan():
    while True:
        read = FileReader.getChar()
        if read == '\n':
            FileReader.incrementLine()
        elif read.isspace():
            pass # Ignore space
        elif read.isalpha():
            newChar = FileReader.getChar()
            while (newChar.isalnum() or newChar in ['_', '-']):
                read += newChar
                newChar = FileReader.getChar()
            FileReader.returnChar(newChar)
            return SymTable.getToken(read.lower())
        elif read.isdigit():
            newChar = FileReader.getChar()
            deci = False
            while (newChar.isdigit() or newChar == '.'):
                if newChar == '.' and deci:
                    Error.minor("Syntax Errror - More than one decimal places in number", "One", ">One")
                elif newChar == '.':
                    deci = True
                read += newChar
                newChar = FileReader.getChar()
            FileReader.returnChar(newChar)
            return LexToken(TokenType.NUMBER, read)
        elif read == "\"" or read == "'":
            readString = ""
            delim = read
            read = FileReader.getChar()
            while read != delim:
                readString += read
                read = FileReader.getChar()
            return LexToken(TokenType.STRING, readString)
        elif read in ['+', '-', '*', '/', '(', ')', '=', ',', ':', '[', ']', '{', '}']:
            nChar = FileReader.getChar()
            if nChar in ['=', '>', '<', '+', '-', '*']:
                return LexToken(TokenType.OPERATION, str(read) + str(nChar))
            else:
                FileReader.returnChar(nChar)
                return LexToken(TokenType.OPERATION, read)
        elif read == ';':
            return LexToken(TokenType.EOS, ";")
        else:
            return LexToken(TokenType.DONE, None)

def match(matchValue):
    global lookahead
    global lastIdentifier

    if lookahead.getTokenValue() == matchValue:
        lookahead = lexan()
        lastIdentifier = False
    else:
        Error.minor("Syntax Error", matchValue, lookahead.getTokenValue())

end = False
def parse():
    global lookahead
    global end
    lookahead = lexan()
    while lookahead.getTokenType() != TokenType.DONE:
        expr()
        if (lookahead.getTokenValue() != ';'):
            expr()
        Emitter.emit(lookahead)
        if not end or lookahead.getTokenValue() == ';':
            match(';')
        end = False

def expr():
    global lookahead
    term()
    while True:
        if lookahead.getTokenType() == TokenType.OPERATION and lookahead.getTokenValue() in ['+', '-']:
            oldLAH = lookahead
            match(lookahead.getTokenValue())
            term()
            Emitter.emit(oldLAH)
        else:
            return

def term():
    global lookahead
    factor()
    while (True):
        if lookahead.getTokenType() == TokenType.OPERATION and lookahead.getTokenValue() in ['*', '/', 'DIV', 'MOD']:
            oldLAH = lookahead
            match(lookahead.getTokenValue())
            factor()
            Emitter.emit(oldLAH)
        else:
            return
            
def factor():
    global lookahead
    
    while (True):
        if lookahead.getTokenType() == TokenType.OPERATION and lookahead.getTokenValue() == '(':
            oldLAH = lookahead
            match('(')
            expr()
            match(')')
            break
        elif lookahead.getTokenType() == TokenType.OPERATION and lookahead.getTokenValue() == '{':
            arrayliteral()
        elif lookahead.getTokenType() == TokenType.NUMBER:
            Emitter.emit(lookahead)
            match(lookahead.getTokenValue())
            break
        elif lookahead.getTokenType() == TokenType.STRING:
            Emitter.emit(lookahead)
            match(lookahead.getTokenValue())
            break
        elif lookahead.getTokenType() == TokenType.IDENTIFIER:
            # Control structures
            if lookahead.getTokenValue() == "if":
                ifstmt()
                return
            elif lookahead.getTokenValue() == "for":
                forstmt()
                return
            
            Emitter.emit(lookahead)
            match(lookahead.getTokenValue())
            if lookahead.getTokenType() == TokenType.OPERATION and lookahead.getTokenValue() == '(':
                parameterList()
            elif lookahead.getTokenType() == TokenType.OPERATION and lookahead.getTokenValue() == '=':
                assignment()
            elif lookahead.getTokenType() == TokenType.OPERATION and lookahead.getTokenValue() == '==':
                comparison()
            elif lookahead.getTokenType() in [TokenType.STRING, TokenType.NUMBER]:
                Emitter.emit(lookahead)
                match(lookahead.getTokenValue())
                Emitter.emit(LexToken(TokenType.CALL, ""))
            else:
                expr()
            break
        else:
            break

def exprblock():
    global lookahead
    global end
    while lookahead.getTokenType() != TokenType.IDENTIFIER or lookahead.getTokenValue() != "end" or lookahead.getTokenValue() != "else" or lookahead.getTokenValue() != "elseif":
        if lookahead.getTokenValue() == "end" or lookahead.getTokenValue() == "else" or lookahead.getTokenValue() == "elseif":
            break
        expr()
        match(';')
    if lookahead.getTokenValue() == "end":
        match(lookahead.getTokenValue())
    end = True

def arrayliteral():
    global lookahead
    match("{")
    Emitter.emit(LexToken(TokenType.ARRYLITERAL, ""))
    while True:
        if lookahead.getTokenValue() != "}":
            if lookahead.getTokenValue() == "[":
                match("[")
                expr()
                match("]")
                assignment()
            Emitter.emit(LexToken(TokenType.SPECIAL, "ARRAY_PUSH"))
            match(",")
        else:
            break
    
    match("}")
	
cntrlno = 0
def ifstmt():
    global lookahead
    global cntrlno
    cntrlno += 1
    localcntrlno = cntrlno
    ifgotonext = 1
    match(lookahead.getTokenValue())
    expr()
    match(":")
    Emitter.emit(LexToken(TokenType.SPECIAL, "GOTOIFNOT {0}?{1}_{2}".format(FileReader.getFileName(), localcntrlno, ifgotonext)))
    exprblock()
    Emitter.emit(LexToken(TokenType.SPECIAL, "GOTO {0}?{1}_END".format(FileReader.getFileName(), localcntrlno)))
    
    while lookahead.getTokenValue() == "elseif":
        Emitter.emit(LexToken(TokenType.SPECIAL, "LABEL {0}?{1}_{2}".format(FileReader.getFileName(), localcntrlno, ifgotonext)))
        match("elseif")
        expr()
        match(":")
        ifgotonext += 1
        Emitter.emit(LexToken(TokenType.SPECIAL, "GOTOIFNOT {0}?{1}_{2}".format(FileReader.getFileName(), localcntrlno, ifgotonext)))
        exprblock()
        Emitter.emit(LexToken(TokenType.SPECIAL, "GOTO {0}?{1}_END".format(FileReader.getFileName(), localcntrlno)))

    if lookahead.getTokenValue() == "else":
        Emitter.emit(LexToken(TokenType.SPECIAL, "LABEL {0}?{1}_{2}".format(FileReader.getFileName(), localcntrlno, ifgotonext)))
        # Else logic
        match("else")
        match(":")
        ifgotonext += 1
        exprblock()
        Emitter.emit(LexToken(TokenType.SPECIAL, "GOTO {0}?{1}_END".format(FileReader.getFileName(), localcntrlno)))
        
    Emitter.emit(LexToken(TokenType.SPECIAL, "LABEL {0}?{1}_{2}".format(FileReader.getFileName(), localcntrlno, ifgotonext)))
    Emitter.emit(LexToken(TokenType.SPECIAL, "LABEL {0}?{1}_END".format(FileReader.getFileName(), localcntrlno)))
    return

def forstmt():
    global lookahead
    global cntrlno
    cntrlno += 1
    localcntrlno = cntrlno
    
    # Collect and match variables
    match(lookahead.getTokenValue())
    loopvariable    =        lookahead
    match(lookahead.getTokenValue())
    match(":")
    loopstart       =       lookahead
    match(lookahead.getTokenValue())
    match("->")
    loopend         =       lookahead
    # We must increase loopend by one to save ugly hax below (As if this isn't ugly hax itself)
    loopend         =       LexToken(TokenType.NUMBER, str(int(loopend.getTokenValue()) + 1))
    loopstep        =       1
    match(lookahead.getTokenValue())

    # Check if non-default step
    if lookahead.getTokenValue() == ":":
        match(":")
        step = lookahead
        match(lookahead.getTokenValue())
    
    match(":")
    
    # Now emit the base loop stuff
    Emitter.emit(loopvariable)
    Emitter.emit(loopstart)
    Emitter.emit(LexToken(TokenType.OPERATION, "="))
    Emitter.emit(LexToken(TokenType.SPECIAL, "LABEL {0}?{1}".format(FileReader.getFileName(), localcntrlno)))


    exprblock()

    Emitter.emit(loopvariable)
    Emitter.emit(loopvariable)
    Emitter.emit(step)
    Emitter.emit(LexToken(TokenType.OPERATION, "+"))
    Emitter.emit(LexToken(TokenType.OPERATION, "="))
    
    Emitter.emit(loopvariable)
    Emitter.emit(loopend)
    Emitter.emit(LexToken(TokenType.OPERATION, "=="))
    Emitter.emit(LexToken(TokenType.SPECIAL, "GOTOIFNOT {0}?{1}".format(FileReader.getFileName(), localcntrlno)))


def comparison():
    global lookahead
    
    if lookahead.getTokenType() == TokenType.OPERATION and lookahead.getTokenValue() in ['==']:
        oldLAH = lookahead
        match(lookahead.getTokenValue())
        factor()
        expr()
        Emitter.emit(oldLAH)
    else:
        return

def assignment():
    global lookahead
    while (True):
        if lookahead.getTokenType() == TokenType.OPERATION and lookahead.getTokenValue() == '=':
            oldLAH = lookahead
            match(lookahead.getTokenValue())
            factor()
            if lookahead.getTokenValue() != ",": # Oh god, this compiler is getting messy and hacky. TODO: Rewrite with a proper grammar defined
                expr()
            Emitter.emit(oldLAH)
        else:
            return

def parameterList():
    global lookahead
    while (True):
        if lookahead.getTokenType() == TokenType.OPERATION and lookahead.getTokenValue() == ',':
            match(',')
            expr()
        elif lookahead.getTokenType() == TokenType.OPERATION and lookahead.getTokenValue() == '(':
            Emitter.emit(lookahead)
            match('(')
            expr()
        elif lookahead.getTokenType() == TokenType.OPERATION and lookahead.getTokenValue() == ')':
            Emitter.emit(lookahead)
            match(')')
            Emitter.emit(LexToken(TokenType.CALL, ""))
            return
        else:
            Error.minor("Syntax error", "Parameter or )", "{0}".format(lookahead.getTokenValue()))
            break
        
class Emitter:
    def emit(token):
        if token.getTokenType() == TokenType.OPERATION:
            Emitter.File.write("OP {0}\n".format(token.getTokenValue()))
        elif token.getTokenType() == TokenType.NUMBER:
            # Simple hax check to see if integer or float
            if not "." in token.getTokenValue():
                Emitter.File.write("PUSH I {0}\n".format(token.getTokenValue()))
            else:
                Emitter.File.write("PUSH F {0}\n".format(token.getTokenValue()))
        elif token.getTokenType() == TokenType.STRING:
            Emitter.File.write("PUSH S {0}\n".format(token.getTokenValue()))
        elif token.getTokenType() == TokenType.CALL:
            Emitter.File.write("CALL\n")
        elif token.getTokenType() == TokenType.ARRYLITERAL:
            Emitter.File.write("PUSH A\n")
        elif token.getTokenType() == TokenType.EOS:
            Emitter.File.write("EOS\n")
        elif token.getTokenType() == TokenType.IDENTIFIER:
            Emitter.File.write("PUSH V {0}\n".format(token.getTokenValue()))
        elif token.getTokenType() == TokenType.SPECIAL:
            Emitter.File.write("CNTRL {0}\n".format(token.getTokenValue()))
        else:
            print("Unknown token {0}".format(token.getTokenValue()))
            Emitter.File.write("ERR")
    def save():
        Emitter.File.write("~EOF")
        Emitter.File.close()

class Error:
    ErrorCount = 0
    
    @staticmethod
    def minor(val, exp = "", got = ""):
        if exp != "" or got != "":
            print("Error: {0} (At line {1})".format(val, FileReader.getLine()), "Expected: {0}".format(exp), " Got: {0}".format(got))
        else:
            print("Error: {0}".format(val))
        Error.ErrorCount += 1

        sys.exit()

    @staticmethod
    def getErrorCount():
        return Error.ErrorCount

    @staticmethod
    def printErrorState():
        print("\n\n /----------------------------------------------------------")
        print(" | {0} errors encountered during execution.".format(Error.ErrorCount))
        print(" \\----------------------------------------------------------\n\n")

def compileFile(fname):
    begin(fname)

'''
start    -> list eof
list     -> expr ; list
          | ¬
expr     -> expr + term
          | expr - term
          | term
term     -> term * factor
          | term / factor
          | term div factor
          | term mod factor
          | factor
factor   -> ( expr )
          | id
          | num

'''
