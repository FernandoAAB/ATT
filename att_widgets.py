"""Componentes vetoriais Tkinter para manter o visual consistente entre sistemas."""
import tkinter as tk
from tkinter import font as tkfont

BG = '#0C111B'
PANEL = '#18232D'
FIELD = '#202D39'
TEXT = '#EAF0F5'
MUTED = '#93A3B0'
GREEN = '#63DDA1'


def rounded(canvas, x1, y1, x2, y2, radius=10, **kwargs):
    r = min(radius, (x2-x1)/2, (y2-y1)/2)
    return canvas.create_polygon(
        x1+r,y1,x2-r,y1,x2,y1,x2,y1+r,x2,y2-r,x2,y2,x2-r,y2,
        x1+r,y2,x1,y2,x1,y2-r,x1,y1+r,x1,y1, smooth=True, splinesteps=18, **kwargs)


def icon(canvas, name, x, y, color=MUTED, size=16):
    s=size/16
    def line(*coords, **kw):
        return canvas.create_line(*[v*s+(x if i%2==0 else y) for i,v in enumerate(coords)], fill=color, width=1.5, **kw)
    def oval(a,b,c,d,**kw):
        return canvas.create_oval(x+a*s,y+b*s,x+c*s,y+d*s,outline=color,width=1.4,**kw)
    if name == 'grid':
        for dx,dy in ((1,1),(9,1),(1,9),(9,9)):
            rounded(canvas,x+dx*s,y+dy*s,x+(dx+5)*s,y+(dy+5)*s,2,fill=color,outline='')
    elif name in ('download','arrow'):
        line(8,1,8,11); line(4,7,8,11,12,7)
        if name=='download': line(2,13,2,15,14,15,14,13)
    elif name=='clock':
        oval(1,1,15,15);line(8,4,8,8,11,10)
    elif name=='apps':
        for dy in (3,8,13): line(1,dy,15,dy)
    elif name=='sliders':
        for dy,dx in ((3,5),(8,11),(13,6)):
            line(1,dy,15,dy);oval(dx-2,dy-2,dx+2,dy+2,fill=canvas.cget('bg'))
    elif name=='settings':
        oval(2,2,14,14);oval(6,6,10,10)
        for coords in ((8,0,8,2),(8,14,8,16),(0,8,2,8),(14,8,16,8)):line(*coords)
    elif name=='refresh':
        canvas.create_arc(x+2*s,y+2*s,x+14*s,y+14*s,start=40,extent=285,style='arc',outline=color,width=1.7)
        line(10,1,14,2,13,6)
    elif name=='search':
        oval(1,1,11,11);line(10,10,15,15)
    elif name=='info':
        oval(1,1,15,15);line(8,7,8,12);oval(7.5,4,8.5,5,fill=color)


class RoundedPanel(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=parent.cget('bg'), **kwargs)
        self.surface = tk.Canvas(self, bg=parent.cget('bg'), highlightthickness=0, borderwidth=0)
        px,py=int(self.cget('padx')),int(self.cget('pady'))
        self.surface.place(x=-px,y=-py,relwidth=1,relheight=1,width=2*px,height=2*py)
        self.tk.call('lower', self.surface._w)
        self.bind('<Configure>', self._paint)

    def _paint(self, _event=None):
        self.surface.delete('all')
        rounded(self.surface,1,1,self.winfo_width()-1,self.winfo_height()-1,13,
                fill=PANEL, outline='#2A3742', width=1)


class RoundedButton(tk.Canvas):
    def __init__(self, parent, text='', command=None, width=150, height=34,
                 primary=False, icon_name=None, nav=False, font='Helvetica'):
        super().__init__(parent,width=width,height=height,bg=PANEL if isinstance(parent,RoundedPanel) else parent.cget('bg'),
                         highlightthickness=0, borderwidth=0, takefocus=1, cursor='hand2')
        self.text, self.command = text, command
        self.primary, self.nav, self.active = primary, nav, False
        self.icon_name, self.family = icon_name, font
        self.disabled, self.hover = False, False
        self.bind('<Configure>',self._paint)
        self.bind('<Button-1>',lambda _:self.invoke())
        self.bind('<Return>',lambda _:self.invoke())
        self.bind('<space>',lambda _:self.invoke())
        self.bind('<Enter>',lambda _:self._hover(True))
        self.bind('<Leave>',lambda _:self._hover(False))
        self.bind('<FocusIn>',self._paint);self.bind('<FocusOut>',self._paint)
        self._paint()

    def configure(self, cnf=None, **kwargs):
        if cnf: kwargs.update(cnf)
        if 'text' in kwargs:self.text=kwargs.pop('text')
        if 'command' in kwargs:self.command=kwargs.pop('command')
        if 'state' in kwargs:self.disabled=kwargs.pop('state')=='disabled'
        if 'style' in kwargs:self.active=kwargs.pop('style')=='Active.Nav.TButton'
        result=super().configure(**kwargs) if kwargs else None
        if hasattr(self,'disabled'): self._paint()
        return result

    config=configure

    def cget(self,key):
        if key=='text':return self.text
        if key=='state':return 'disabled' if self.disabled else 'normal'
        return super().cget(key)

    def instate(self, states):
        return all(self.disabled if state=='disabled' else not self.disabled if state=='!disabled' else True for state in states)

    def invoke(self):
        if not self.disabled and self.command:return self.command()

    def _hover(self,value):self.hover=value;self._paint()

    def _paint(self,_event=None):
        self.delete('all')
        w=self.winfo_width() if self.winfo_width()>1 else int(super().cget('width'))
        h=self.winfo_height() if self.winfo_height()>1 else int(super().cget('height'))
        fill=('#24483E' if self.active else '#101A27') if self.nav else GREEN if self.primary else '#20332E'
        if self.disabled:fill=FIELD
        elif self.hover:fill='#79EAB4' if self.primary else '#29443D'
        rounded(self,1,1,w-1,h-1,8,fill=fill,outline=('#33443C' if not self.nav else ''))
        fg='#123C30' if self.primary and not self.disabled else '#697B89' if self.disabled else TEXT if not self.nav or self.active else MUTED
        if self.nav:
            if self.active:rounded(self,1,5,5,h-5,2,fill=GREEN,outline='')
            icon(self,self.icon_name or 'grid',15,(h-16)/2,GREEN if self.active else MUTED)
            self.create_text(43,h/2,text=self.text,fill=fg,anchor='w',font=(self.family,-12,'bold' if self.active else 'normal'),tags='button_text')
        else:
            if self.icon_name:icon(self,self.icon_name,16,(h-16)/2,fg)
            self.create_text(w/2+(9 if self.icon_name else 0),h/2,text=self.text,fill=fg,
                             font=(self.family,-12,'bold' if self.primary else 'normal'),tags='button_text')
        if self.focus_get()==self:rounded(self,2,2,w-2,h-2,8,outline=GREEN,fill='',width=1)


class Choice(RoundedButton):
    def __init__(self,parent,variable,values,width=112,font='Helvetica'):
        self.variable,self.values=variable,values
        self.minimum_width=width
        metrics=tkfont.Font(root=parent,family=font,size=-12)
        width=min(220,max(width,max((metrics.measure(value) for value in (*values,variable.get())),default=0)+40))
        super().__init__(parent,text=variable.get(),command=self.choose,width=width,height=30,font=font)
        self.trace=variable.trace_add('write',lambda *_:self.configure(text=variable.get()))
        self.bind('<Destroy>',self._destroy,add='+')
    def _destroy(self,event):
        if event.widget==self:
            self.variable.trace_remove('write',self.trace)
    def configure(self,cnf=None,**kwargs):
        if 'values' in kwargs:
            self.values=kwargs.pop('values')
            metrics=tkfont.Font(root=self,family=self.family,size=-12)
            kwargs['width']=min(220,max(self.minimum_width,max((metrics.measure(value) for value in (*self.values,self.variable.get())),default=0)+40))
        return super().configure(cnf,**kwargs)
    def choose(self):
        menu=tk.Menu(self,tearoff=False,bg=FIELD,fg=TEXT,activebackground='#264C3F',activeforeground=TEXT,
                     font=(self.family,-11))
        for value in self.values:menu.add_command(label=value,command=lambda v=value:self.variable.set(v))
        try:menu.tk_popup(self.winfo_rootx(),self.winfo_rooty()+self.winfo_height())
        finally:menu.grab_release()
    def _paint(self,event=None):
        super()._paint(event)
        if hasattr(self,'family'):
            w=self.winfo_width() if self.winfo_width()>1 else int(super().cget('width'))
            metrics=tkfont.Font(root=self,family=self.family,size=-12)
            text=self.variable.get()
            if metrics.measure(text)>max(0,w-36):
                while text and metrics.measure(text+'…')>max(0,w-36):text=text[:-1]
                text+='…'
            self.coords('button_text',12,15)
            self.itemconfigure('button_text',text=text,anchor='w')
            self.create_line(w-15,13,w-11,17,w-7,13,fill=MUTED,width=1)


class Toggle(tk.Canvas):
    def __init__(self,parent,variable,command,text,font='Helvetica',switch=True,width=300):
        super().__init__(parent,width=width,height=26,bg=PANEL,highlightthickness=0,takefocus=1,cursor='hand2')
        self.variable,self.command,self.text,self.family,self.switch=variable,command,text,font,switch
        self.disabled=False
        self.trace=variable.trace_add('write',lambda *_:self.paint())
        self.bind('<Button-1>',lambda _:self.invoke());self.bind('<space>',lambda _:self.invoke())
        self.bind('<Destroy>',self._destroy,add='+');self.paint()
    def _destroy(self,event):
        if event.widget==self:self.variable.trace_remove('write',self.trace)
    def configure(self,cnf=None,**kw):
        if 'state' in kw:self.disabled=kw.pop('state')=='disabled'
        result=super().configure(cnf,**kw) if cnf or kw else None
        self.paint();return result
    def invoke(self):
        if not self.disabled:
            self.variable.set(not self.variable.get())
            self.command()
    def paint(self):
        self.delete('all');on=self.variable.get();c=GREEN if on else '#344552'
        if self.switch:
            rounded(self,1,6,28,21,8,fill=c,outline='')
            self.create_oval(15 if on else 3,8,25 if on else 13,18,fill='#D8F8E8' if on else '#80919C',outline='')
        else:
            rounded(self,4,6,19,21,3,fill=FIELD,outline='#40515E')
            if on:self.create_line(7,13,11,17,17,9,fill=GREEN,width=2)
        self.create_text(36 if self.switch else 29,13,text=self.text,anchor='w',
                         fill='#687C88' if self.disabled else TEXT,font=(self.family,-11))


class Search(tk.Frame):
    def __init__(self,parent,variable,font='Helvetica',width=220):
        super().__init__(parent,bg=PANEL,width=width,height=30)
        self.pack_propagate(False)
        canvas=tk.Canvas(self,bg=PANEL,highlightthickness=0)
        canvas.place(x=0,y=0,relwidth=1,relheight=1)
        def paint(event):
            canvas.delete('all');rounded(canvas,1,1,event.width-1,29,6,fill='#0E1A24',outline='#2B3A44')
            icon(canvas,'search',10,7,MUTED,15)
        canvas.bind('<Configure>',paint)
        entry=tk.Entry(self,textvariable=variable,bg='#0E1A24',fg=TEXT,insertbackground=TEXT,
                        relief='flat',font=(font,-11),highlightthickness=0)
        entry.place(x=32,y=5,relwidth=1,width=-40,height=20)
        hint=tk.Label(self,text='Pesquisar por aplicativo...',bg='#0E1A24',fg='#748592',font=(font,-11),anchor='w')
        def show(*_):
            if not variable.get() and entry.focus_get()!=entry:hint.place(x=32,y=5,relwidth=1,width=-40,height=20)
            else:hint.place_forget()
        self.trace=variable.trace_add('write',show)
        entry.bind('<FocusIn>',show);entry.bind('<FocusOut>',show)
        hint.bind('<Button-1>',lambda _:entry.focus_set())
        self.bind('<Destroy>',lambda event:variable.trace_remove('write',self.trace) if event.widget==self else None)
        show()


def description(identifier):
    return {'Google.Chrome':'Navegador web','Mozilla.Firefox':'Navegador web',
            'Microsoft.VisualStudioCode':'Editor de código','7zip.7zip':'Compactador de arquivos',
            'VideoLAN.VLC':'Reprodutor multimídia'}.get(identifier,identifier)


class UpdateTable(tk.Canvas):
    """Tabela vetorial com a API de seleção usada pelo controlador."""
    def __init__(self,parent,font='Helvetica',details=None):
        super().__init__(parent,bg=PANEL,highlightthickness=0,takefocus=1,height=230)
        self.family,self.details=font,details
        self.rows={};self.selected=();self.focused='';self.offset=0;self._pending=None
        self.bind('<Configure>',lambda _:self.draw())
        self.bind('<MouseWheel>',lambda e:self.scroll(-1 if e.delta>0 else 1))
        self.bind('<Button-4>',lambda _:self.scroll(-1));self.bind('<Button-5>',lambda _:self.scroll(1))
        self.bind('<B1-Motion>',lambda e:self.drag_scroll(e.y) if e.x>self.winfo_width()-8 else None)
        self.bind('<KeyPress-Up>',lambda _:self.move(-1));self.bind('<KeyPress-Down>',lambda _:self.move(1))
        self.bind('<Destroy>',self._destroy,add='+')
    def _destroy(self,event):
        if event.widget==self and self._pending:self.after_cancel(self._pending)
    def defer(self):
        if self._pending is None:self._pending=self.after_idle(self.draw)
    def get_children(self):return tuple(self.rows)
    def delete(self,*keys):
        for key in keys:self.rows.pop(key,None)
        self.selected=tuple(k for k in self.selected if k in self.rows);self.defer()
    def insert(self,parent,index,iid,values,tags=()):
        self.rows[iid]=values;self.defer();return iid
    def exists(self,key):return key in self.rows
    def selection(self):return self.selected
    def selection_set(self,key):
        self.selected=(key,) if key in self.rows else ();self.focused=key
        self.event_generate('<<TreeviewSelect>>',when='tail');self.defer()
    def focus(self,key=None):
        if key is not None:self.focused=key
        return self.focused
    def identify_column(self,x):return '#1' if x<38 else '#6' if x>self.winfo_width()-30 else '#2'
    def identify_row(self,y):
        row=(int(y)-30)//38
        visible=max(0,(self.winfo_height()-30)//38)
        if not (0<=row<visible and 30<=y<self.winfo_height()):return ''
        i=row+self.offset
        keys=list(self.rows)
        return keys[i] if 0<=i<len(keys) else ''
    def bbox(self,key,column=None):
        if key not in self.rows:return ()
        y=30+(list(self.rows).index(key)-self.offset)*38
        return (0,y,38,38) if column=='select' else (0,y,self.winfo_width(),38)
    def see(self,key):
        if key not in self.rows:return
        index=list(self.rows).index(key);visible=max(1,(self.winfo_height()-30)//38)
        if index<self.offset:self.offset=index
        elif index>=self.offset+visible:self.offset=index-visible+1
        self.defer()
    def drag_scroll(self,y):
        visible=max(1,(self.winfo_height()-30)//38)
        self.offset=max(0,min(max(0,len(self.rows)-visible),int((y-30)/max(1,self.winfo_height()-30)*len(self.rows))))
        self.draw()
    def scroll(self,delta):
        maximum=max(0,len(self.rows)-max(1,(self.winfo_height()-30)//38))
        self.offset=max(0,min(maximum,self.offset+delta));self.draw()
    def move(self,delta):
        keys=list(self.rows)
        if not keys:return
        index=keys.index(self.focused) if self.focused in keys else (-1 if delta>0 else len(keys))
        key=keys[max(0,min(len(keys)-1,index+delta))]
        self.selection_set(key);self.see(key);return 'break'
    def _short(self,text,pixels,size=-11):
        font=tkfont.Font(family=self.family,size=size)
        if font.measure(text)<=pixels:return text
        while text and font.measure(text+'…')>pixels:text=text[:-1]
        return text+'…'
    def draw(self):
        if self._pending:
            self.after_cancel(self._pending);self._pending=None
        super().delete('all')
        w,h=self.winfo_width(),self.winfo_height()
        if w<10:return
        rounded(self,0,0,w,29,5,fill=FIELD,outline='')
        rounded(self,15,11,22,18,1,fill=PANEL,outline='#6F808A')
        eligible=[values for values in self.rows.values() if values[0]!='—']
        if eligible and all(values[0]=='[x]' for values in eligible):
            self.create_line(16,14,18,17,22,11,fill=GREEN,width=1.2)
        for x,label in ((46,'APLICATIVO'),(w*.445,'INSTALADA'),(w*.59,'DISPONÍVEL'),(w*.745,'STATUS')):
            self.create_text(x,14,text=label,anchor='w',fill=MUTED,font=(self.family,-9))
        visible=max(1,(h-30)//38)
        self.offset=min(self.offset,max(0,len(self.rows)-visible))
        for index,(key,values) in enumerate(list(self.rows.items())[self.offset:self.offset+visible]):
            check,name,installed,available,status=values;y=30+index*38
            if key in self.selected:self.create_rectangle(0,y,w,y+38,fill='#1B2B35',outline='')
            self.create_line(10,y+38,w-10,y+38,fill='#23313B')
            rounded(self,15,y+15,22,y+22,1,fill='#183A30' if check=='[x]' else PANEL,outline='#5A7C75' if check=='[x]' else '#576A77')
            if check=='[x]':self.create_line(16,y+18,18,y+21,22,y+15,fill=GREEN,width=1.2)
            identifier=getattr(self,'identifiers',{}).get(key,'')
            color={'Google.Chrome':'#D0B973','Microsoft.VisualStudioCode':'#7DB5E0','Mozilla.Firefox':'#A4A4D0'}.get(identifier,'#8FC7C3')
            letter={'Google.Chrome':'C','Mozilla.Firefox':'F','Microsoft.VisualStudioCode':'V'}.get(identifier,name[0].upper())
            rounded(self,44,y+6,72,y+34,5,fill='#24343E',outline='')
            self.create_text(58,y+20,text=letter,fill=color,font=(self.family,-14))
            self.create_text(82,y+13,text=self._short(name,w*.445-88),anchor='w',fill=TEXT,font=(self.family,-12))
            identifier=getattr(self,'identifiers',{}).get(key,'')
            self.create_text(82,y+29,text=self._short(description(identifier),w*.445-88,-9),anchor='w',fill=MUTED,font=(self.family,-9))
            for x,text in ((w*.445,installed),(w*.59,available)):
                self.create_text(x,y+20,text=self._short(text,w*.14-8,-10),anchor='w',fill=TEXT if x==w*.59 else MUTED,
                                 font=(self.family,-10,'bold' if x==w*.59 else 'normal'))
            label='Disponível' if status=='Pendente' else status
            fill,fg=('#243C50','#A7C7E4') if status=='Pendente' else ('#473538','#F0A7AD') if status=='Falhou' else ('#254A3C',GREEN)
            pillw=min(w*.16,104)
            rounded(self,w*.745,y+10,w*.745+pillw,y+30,10,fill=fill,outline='')
            self.create_text(w*.745+8,y+20,text=self._short(label,pillw-12,-9),anchor='w',fill=fg,font=(self.family,-9))
            icon(self,'info',w-23,y+14,MUTED,12)
        if len(self.rows)>visible:
            self.create_rectangle(w-3,32,w-1,h-3,fill=FIELD,outline='')
            top=32+(h-38)*self.offset/len(self.rows)
            self.create_rectangle(w-3,top,w-1,top+max(10,(h-38)*visible/len(self.rows)),fill='#566B77',outline='')
