"""Layout e navegação do painel ATT."""
from datetime import datetime
import platform
import tkinter as tk
from tkinter import font as tkfont, ttk
from att_widgets import RoundedPanel, RoundedButton, Choice, Toggle, Search, UpdateTable, rounded

BG = '#0C111B'
PANEL = '#18232D'
FIELD = '#202F3C'
TEXT = '#EAF0F5'
MUTED = '#9BAEBB'
GREEN = '#63DDA1'


class Dashboard:
    def __init__(self, app):
        self.app = app
        self.view = 'Visão geral'
        self.pages = {}
        self.nav = {}
        self.status_filter = tk.StringVar(value='Todos os status')
        self.source_filter = tk.StringVar(value='Todas as origens')
        self.order = tk.StringVar(value='Ordenar por')
        self.type_filter = tk.StringVar(value='Todos os tipos')
        self.apps_filter = tk.StringVar()
        self.stop_toggle = tk.BooleanVar(value=False)

    def label(self, parent, text='', size=10, color=TEXT, bg=PANEL, bold=False, **kwargs):
        return tk.Label(parent, text=text, bg=bg, fg=color,
                        font=(self.font, -size, 'bold' if bold else 'normal'), **kwargs)

    def panel(self, parent, **kwargs):
        return RoundedPanel(parent, **kwargs)

    def build(self):
        a, root = self.app, self.app.root
        self.font = 'Segoe UI' if 'Segoe UI' in tkfont.families(root) else 'Helvetica'
        root.title('ATT — Central de atualizações')
        root.geometry('1280x720')
        root.minsize(900, 720)
        root.configure(bg=BG)
        root.rowconfigure(1, weight=1)
        root.columnconfigure(1, weight=1)
        style = ttk.Style(root)
        style.theme_use('clam')
        style.configure('TButton',background=FIELD,foreground=TEXT,padding=8,font=(self.font,-11))
        style.configure('TEntry',fieldbackground='#101B25',foreground=TEXT,insertcolor=TEXT,padding=7)
        style.configure('TCheckbutton',background=PANEL,foreground=TEXT,font=(self.font,-12),padding=5)
        style.map('TCheckbutton',background=[('active',PANEL)])
        style.configure('Treeview',background=PANEL,fieldbackground=PANEL,foreground=TEXT,
                        rowheight=36,borderwidth=0,font=(self.font,-12))
        style.map('Treeview',background=[('selected','#24483F')],foreground=[('selected',TEXT)])
        style.configure('Treeview.Heading',background=FIELD,foreground=MUTED,padding=8,font=(self.font,-10))
        style.configure('Vertical.TScrollbar',background=FIELD,troughcolor=PANEL,borderwidth=0,arrowsize=9)
        style.configure('Horizontal.TScrollbar',background=FIELD,troughcolor=PANEL,borderwidth=0,arrowsize=9)
        style.configure('Horizontal.TProgressbar',background=GREEN,troughcolor='#30434E',
                        borderwidth=0,bordercolor=PANEL,lightcolor=GREEN,darkcolor=GREEN,thickness=6)

        top=tk.Frame(root,bg='#121C25',height=42)
        top.grid(row=0,column=0,columnspan=2,sticky='ew');top.pack_propagate(False)
        logo=tk.Canvas(top,width=24,height=24,bg='#121C25',highlightthickness=0)
        logo.pack(side='left',padx=(15,7));rounded(logo,1,1,23,23,6,fill=GREEN,outline='')
        logo.create_text(12,12,text='A',font=(self.font,-17,'bold'),fill='#16452F')
        self.label(top,'ATT',14,bg='#121C25',bold=True).pack(side='left')
        self.label(top,' / Central de Atualizações',11,MUTED,'#121C25').pack(side='left')
        lights=tk.Canvas(top,width=34,height=20,bg='#121C25',highlightthickness=0)
        lights.pack(side='right',padx=(32,16));lights.create_oval(4,5,14,15,fill=GREEN,outline='')
        lights.create_oval(23,8,27,12,fill='#71818F',outline='')
        self.label(top,f'{platform.system()} {platform.release()}  ·  Este computador',10,MUTED,'#121C25').pack(side='right')

        side=tk.Frame(root,bg='#101A27',width=180)
        side.grid(row=1,column=0,sticky='ns');side.pack_propagate(False)
        self.label(side,'ESPAÇO DE TRABALHO',8,MUTED,'#101A27').pack(anchor='w',padx=17,pady=(18,5))
        for view, symbol in zip(('Visão geral','Atualizações','Histórico','Aplicativos','Automação','Configurações'),
                                ('grid','download','clock','apps','sliders','settings')):
            button=RoundedButton(side,text=view,command=lambda name=view:self.show(name),width=160,height=36,
                                 nav=True,icon_name=symbol,font=self.font)
            button.pack(fill='x',padx=10,pady=2);self.nav[view]=button
        tk.Frame(side,bg='#26323C',height=1).pack(fill='x',padx=16,pady=(34,15))
        self.label(side,'ESTADO DA CONSULTA',8,MUTED,'#101A27').pack(anchor='w',padx=18)
        self.device_status=self.label(side,'Aguardando verificação',10,GREEN,'#101A27',wraplength=148,justify='left')
        self.device_status.pack(anchor='w',padx=18,pady=(12,8))
        self.label(side,'Última verificação',9,MUTED,'#101A27').pack(anchor='w',padx=18)
        self.last_check_label=self.label(side,'Ainda não verificado',10,TEXT,'#101A27',wraplength=148,justify='left')
        self.last_check_label.pack(anchor='w',padx=18,pady=4)
        tip=self.panel(side,height=96,padx=12,pady=12)
        tip.pack(side='bottom',fill='x',padx=12,pady=(0,28));tip.pack_propagate(False)
        self.label(tip,'ATUALIZAÇÃO INTELIGENTE',8,GREEN).pack(anchor='w')
        self.label(tip,'Mantenha seus programas\nsempre em dia.',10,MUTED,justify='left').pack(anchor='w',pady=7)
        link=self.label(tip,'Saiba mais →',10,GREEN,cursor='hand2')
        link.pack(anchor='w');link.bind('<Button-1>',lambda _:self.show('Automação'))

        page=tk.Frame(root,bg=BG,padx=20,pady=0)
        page.grid(row=1,column=1,sticky='nsew',padx=(0,14),pady=(20,10))
        page.columnconfigure(0,weight=1);page.rowconfigure(1,weight=1)
        header=tk.Frame(page,bg=BG,height=52)
        header.grid(row=0,column=0,sticky='ew',pady=(0,12));header.pack_propagate(False)
        a.refresh_button=RoundedButton(header,text='Verificar atualizações',command=a.refresh,primary=True,
                                       width=206,height=40,icon_name='refresh',font=self.font)
        a.refresh_button.pack(side='right',anchor='n',pady=4)
        self.heading=self.label(header,'Visão geral',26,bg=BG,bold=True);self.heading.pack(anchor='w')
        self.subtitle=self.label(header,'Gerencie versões, instale atualizações e acompanhe cada etapa.',12,MUTED,BG)
        self.subtitle.pack(anchor='w',pady=(3,0))
        container=tk.Frame(page,bg=BG);container.grid(row=1,column=0,sticky='nsew')
        container.rowconfigure(0,weight=1);container.columnconfigure(0,weight=1)
        overview=tk.Frame(container,bg=BG);overview.grid(row=0,column=0,sticky='nsew')
        overview.columnconfigure(0,weight=1);overview.rowconfigure(1,weight=1)
        self.pages['Visão geral']=overview
        self.stats=tk.Frame(overview,bg=BG,height=90)
        self.stats.grid(row=0,column=0,sticky='ew',pady=(0,14));self.stats.grid_propagate(False)
        self.compact_stats=self.label(overview,'',10,MUTED,BG,anchor='w',wraplength=620)
        self.compact_stats.grid(row=0,column=0,sticky='ew',pady=(0,12));self.compact_stats.grid_remove()
        self.values=[]
        for index,(title,note,color) in enumerate((
            ('PROGRAMAS INSTALADOS','Detectados no dispositivo','#8CB5F4'),
            ('ATUALIZAÇÕES DISPONÍVEIS','Elegíveis para atualização','#F2C069'),
            ('ATUALIZADOS','Registrados pelo ATT',GREEN),
            ('ÚLTIMA VERIFICAÇÃO','Consulta de atualizações','#B5A2EC'))):
            self.stats.columnconfigure(index,weight=1,uniform='metric')
            card=self.panel(self.stats,height=90)
            card.grid(row=0,column=index,sticky='nsew',padx=(0 if index==0 else 6,0 if index==3 else 6));card.grid_propagate(False)
            symbol=tk.Canvas(card,width=30,height=30,bg=PANEL,highlightthickness=0)
            symbol.place(x=16,y=16);rounded(symbol,0,0,30,30,7,fill='#233640',outline='')
            symbol.create_oval(9,9,21,21,fill=color,outline='')
            self.label(card,title,8,MUTED).place(x=53,y=14)
            value=self.label(card,'—',26,TEXT,bold=True);value.place(x=14,y=44)
            note_label=self.label(card,note,9,MUTED)
            note_label.place(x=88 if index==3 else 76,y=63)
            if index==3:self.check_note=note_label
            self.values.append(value)
        a.completed_counter=self.values[2]
        middle=tk.Frame(overview,bg=BG);middle.grid(row=1,column=0,sticky='nsew')
        middle.columnconfigure(0,weight=1);middle.rowconfigure(0,weight=1)
        table_panel=self.panel(middle,padx=16,pady=16)
        table_panel.grid(row=0,column=0,sticky='nsew');table_panel.columnconfigure(0,weight=1);table_panel.rowconfigure(2,weight=1)
        table_title=tk.Frame(table_panel,bg=PANEL,height=24)
        table_title.grid(row=0,column=0,sticky='ew',pady=(0,10));table_title.pack_propagate(False)
        self.label(table_title,'Atualizações disponíveis',16,bold=True).pack(side='left')
        self.available_badge=self.label(table_title,'0',10,GREEN,'#254B3D',padx=10)
        self.available_badge.pack(side='left',padx=25)
        filters=tk.Frame(table_panel,bg=PANEL,height=30)
        filters.grid(row=1,column=0,sticky='ew',pady=(0,12));filters.columnconfigure(3,weight=1)
        Search(filters,a.filter_text,self.font,width=224).grid(row=0,column=0,padx=(0,16))
        self.type_combo=Choice(filters,self.type_filter,('Todos os tipos','Navegadores','Desenvolvimento','Utilitários','Multimídia','Outros'),width=104,font=self.font)
        self.type_combo.grid(row=0,column=1,padx=(0,8))
        Choice(filters,self.order,('Ordenar por','Nome A–Z','Nome Z–A','Status'),width=104,font=self.font).grid(row=0,column=2)
        self.source_combo=Choice(filters,self.source_filter,('Todas as origens',),width=130,font=self.font)
        self.source_combo.grid(row=1,column=0,sticky='w',pady=8);self.source_combo.grid_remove()
        self.status_combo=Choice(filters,self.status_filter,('Todos os status','Pendentes','Selecionados','Atualizados','Falhas','Bloqueados'),width=126,font=self.font)
        self.status_combo.grid(row=1,column=1,columnspan=2,sticky='w',pady=8);self.status_combo.grid_remove()
        a.select_button=RoundedButton(filters,text='Selecionar todos',command=self.toggle_all,width=172,height=30,font=self.font)
        a.select_button.grid(row=0,column=4,sticky='e',padx=(12,0))
        a.clear_button=RoundedButton(filters,text='Limpar seleção',command=a.clear_selection,font=self.font)
        area=tk.Frame(table_panel,bg=PANEL);area.grid(row=2,column=0,sticky='nsew');area.rowconfigure(0,weight=1);area.columnconfigure(0,weight=1)
        a.tree=UpdateTable(area,self.font);a.tree.grid(row=0,column=0,sticky='nsew')
        a.tree.bind('<Button-1>',a._click_row);a.tree.bind('<space>',a._space_row)
        a.tree.bind('<<TreeviewSelect>>',a._show_details)
        a.tree.bind('<Return>',lambda _:self.show_package())
        a.empty_label=self.label(area,'Clique em Verificar atualizações para começar.',11,MUTED,wraplength=330,justify='center')
        a.empty_label.place(relx=.5,rely=.55,anchor='center')
        a.empty_label.bind('<Button-1>',lambda _:self.show_package() if a.query_failed else None)
        a.detail_box=tk.Text(table_panel,height=2,wrap='word',bg=PANEL,fg=MUTED,relief='flat',font=(self.font,-11))
        a._set_details(a.last_output)

        self.execution=self.panel(middle,width=248)
        self.execution.grid(row=0,column=1,sticky='ns',padx=(12,0));self.execution.grid_propagate(False)
        queue_header=tk.Frame(self.execution,bg=PANEL)
        queue_header.place(x=16,y=20,relwidth=1,width=-32,height=24)
        self.label(queue_header,'Central de execução',14,bold=True).pack(side='left')
        self.execution_state=self.label(queue_header,'EM ESPERA',8,MUTED,'#293D4B',padx=6,pady=3)
        self.execution_state.pack(side='right')
        self.label(self.execution,'Fila de atualizações',10,MUTED).place(x=16,y=60)
        self.queue_count=self.label(self.execution,'Nenhum programa selecionado',12,bold=True,wraplength=210,justify='left')
        self.queue_count.place(x=16,y=83)
        self.queue_list=tk.Text(self.execution,bg=PANEL,fg=MUTED,font=(self.font,-11),wrap='word',
                                relief='flat',highlightthickness=0,height=8,width=20,spacing1=0,spacing3=0)
        self.queue_list.place(x=16,y=108,relwidth=1,width=-32,relheight=1,height=-207)
        self.queue_list.tag_configure('name',foreground=TEXT,font=(self.font,-11))
        self.queue_list.tag_configure('detail',foreground=MUTED,font=(self.font,-9),lmargin1=16,lmargin2=16)
        tk.Frame(self.execution,bg='#2B3A45',height=1).place(x=16,rely=1,y=-84,relwidth=1,width=-32)
        progress_title=tk.Frame(self.execution,bg=PANEL)
        progress_title.place(x=16,rely=1,y=-75,relwidth=1,width=-32,height=16)
        self.label(progress_title,'Progresso total',10,MUTED).pack(side='left')
        self.percent=self.label(progress_title,'0%',10,bold=True);self.percent.pack(side='right')
        a.progress=ttk.Progressbar(self.execution,mode='determinate')
        a.progress.place(x=16,rely=1,y=-53,relwidth=1,width=-32,height=7)
        self.label(self.execution,textvariable=a.progress_text,size=9,color=MUTED,wraplength=210,justify='left').place(x=16,rely=1,y=-35)

        for view in ('Histórico','Aplicativos','Automação','Configurações'):
            frame=self.panel(container,padx=20,pady=18);frame.grid(row=0,column=0,sticky='nsew')
            frame.columnconfigure(0,weight=1);frame.rowconfigure(1,weight=1);self.pages[view]=frame
        self._build_history();self._build_apps();self._build_settings()
        self.options=self.panel(page,height=114)
        self.options.grid(row=2,column=0,sticky='ew',pady=(12,0));self.options.pack_propagate(False)
        self.label(self.options,'Opções de execução',14,bold=True).place(x=18,y=16)
        self.compact_progress=self.label(self.options,textvariable=a.progress_text,size=9,color=MUTED)
        Toggle(self.options,a.auto_update,a._save_preference,'Atualizar ao abrir o ATT',font=self.font,width=270).place(x=18,y=40)
        self.label(self.options,'Verificar automaticamente ao iniciar o programa',9,MUTED).place(x=53,y=70)
        a.stop_button=Toggle(self.options,self.stop_toggle,a.request_stop,'Parar após este pacote',font=self.font,switch=False,width=250)
        a.stop_button.place(x=350,y=40)
        self.stop_note=self.label(self.options,'Finaliza os itens em execução antes de parar',9,MUTED)
        self.stop_note.place(x=379,y=70)
        a.update_button=RoundedButton(self.options,text='Atualizar selecionados',command=a.start_updates,primary=True,
                                      width=250,height=44,icon_name='download',font=self.font)
        a.update_button.place(relx=1,x=-22,y=39,anchor='ne')
        status=self.label(page,textvariable=a.status_text,size=9,color=MUTED,bg=BG,wraplength=800,justify='left',anchor='w')
        status.grid(row=3,column=0,sticky='ew',pady=(9,0));status.bind('<Configure>',lambda e:status.configure(wraplength=max(100,e.width)))
        for variable in (self.status_filter,self.source_filter,self.type_filter,self.order):
            variable.trace_add('write',lambda *_:a._render_rows())
        self.apps_filter.trace_add('write',lambda *_:self.render_apps())
        root.bind('<Configure>',self._resize,add='+');self.show('Visão geral')

    def toggle_all(self):
        a=self.app
        eligible={key for key in a.packages if a._eligible(key)}
        a.clear_selection() if eligible and eligible<=a.selected else a.select_all()

    def show_package(self):
        if self.app.tree.selection():self.app._show_details()
        popup=tk.Toplevel(self.app.root);popup.title('Detalhes da atualização');popup.geometry('640x340')
        popup.configure(bg=BG);popup.transient(self.app.root)
        text=tk.Text(popup,bg=PANEL,fg=TEXT,wrap='word',relief='flat',font=(self.font,-12),padx=15,pady=15)
        text.pack(fill='both',expand=True,padx=12,pady=12)
        text.insert('1.0',self.app.detail_box.get('1.0','end'));text.configure(state='disabled')

    def make_tree(self, parent, columns, headings, widths):
        parent.rowconfigure(0, weight=1)
        parent.columnconfigure(0, weight=1)
        tree = ttk.Treeview(parent, columns=columns, show='headings', selectmode='browse', height=5)
        for column, heading, width in zip(columns, headings, widths):
            tree.heading(column, text=heading, anchor='w')
            tree.column(column, width=width, minwidth=width, stretch=False)
        tree.grid(row=0, column=0, sticky='nsew')
        scroll = ttk.Scrollbar(parent, orient='vertical', command=tree.yview)
        scroll.grid(row=0, column=1, sticky='ns')
        horizontal = ttk.Scrollbar(parent, orient='horizontal', command=tree.xview)
        horizontal.grid(row=1, column=0, sticky='ew')
        tree.configure(yscrollcommand=scroll.set, xscrollcommand=horizontal.set)
        return tree

    def _build_history(self):
        frame = self.pages['Histórico']
        self.label(frame, 'Execuções registradas neste usuário (até 1.000 registros)', 11, bold=True).grid(row=0, column=0, sticky='w', pady=(0, 15))
        body = tk.Frame(frame, bg=PANEL)
        body.grid(row=1, column=0, sticky='nsew')
        self.history_tree = self.make_tree(body, ('time', 'name', 'version', 'status'),
                                           ('DATA / HORA', 'APLICATIVO', 'DESTINO', 'RESULTADO'), (155, 210, 100, 165))
        self.history_tree.column('name', minwidth=120, stretch=True)
        self.history_details = tk.Text(frame, height=5, wrap='word', bg=FIELD, fg=TEXT,
                                       relief='flat', font=(self.font, 10))
        self.history_details.grid(row=2, column=0, sticky='ew', pady=(12, 0))
        self.history_details.configure(state='disabled')
        self.history_tree.bind('<<TreeviewSelect>>', self._history_selected)

    def _build_apps(self):
        frame = self.pages['Aplicativos']
        ttk.Entry(frame, textvariable=self.apps_filter).grid(row=0, column=0, sticky='ew', pady=(0, 15))
        body = tk.Frame(frame, bg=PANEL)
        body.grid(row=1, column=0, sticky='nsew')
        self.apps_tree = self.make_tree(body, ('name', 'id', 'version', 'source'),
                                        ('APLICATIVO', 'IDENTIFICADOR', 'VERSÃO', 'ORIGEM'), (210, 240, 100, 100))
        self.apps_tree.column('name', minwidth=110, stretch=True)
        self.inventory_info = self.label(frame, 'Verifique as atualizações para consultar o inventário.', 10, MUTED, wraplength=650, justify='left')
        self.inventory_info.grid(row=2, column=0, sticky='w', pady=12)

    def _build_settings(self):
        a = self.app
        auto = self.pages['Automação']
        self.label(auto, 'Atualização automática opcional', 16, bold=True).grid(row=0, column=0, sticky='w')
        body = tk.Frame(auto, bg=PANEL)
        body.grid(row=1, column=0, sticky='new', pady=20)
        ttk.Checkbutton(body, text='Atualizar todos os pendentes ao abrir o ATT', variable=a.auto_update,
                        command=a._save_preference).pack(anchor='w')
        self.label(body, 'A alteração vale para a próxima abertura. O painel permanece visível durante as instalações.\n\n'
                   'O ATT não inicia com o Windows. Para parar uma fila em andamento, use “Parar após este pacote”.\n'
                   'O instalador atual é concluído antes da parada; ele não é encerrado à força.', 11, MUTED,
                   wraplength=580, justify='left').pack(anchor='w', pady=20)
        settings = self.pages['Configurações']
        self.label(settings, 'Armazenamento e funcionamento', 16, bold=True).grid(row=0, column=0, sticky='w')
        path = str(a.preference_path or '%LOCALAPPDATA%/ATT/config.json')
        self.label(settings, f'Preferências: {path}\nHistórico: {a.activity.path or "indisponível"}\n\n'
                   'Instalações silenciosas via winget, em sequência. Contratos não são aceitos automaticamente.\n'
                   'Atualizações que exigem interação mostram o motivo nos detalhes.\n\n'
                   'Os filtros organizam por origem e estado real. O winget não fornece uma classificação de recomendações.\n'
                   'O estado exibido é o da consulta; o ATT não monitora antivírus ou a proteção do Windows.',
                   11, MUTED, wraplength=600, justify='left').grid(row=1, column=0, sticky='nw', pady=20)

    def show(self, view):
        self.view = view
        for name, button in self.nav.items():
            button.configure(style='Active.Nav.TButton' if name == view else 'Nav.TButton')
        self.heading.configure(text=view)
        descriptions = {'Histórico': 'Resultados e detalhes das atualizações executadas pelo ATT.',
                        'Aplicativos': 'Inventário detectado pelo winget na última verificação.',
                        'Automação': 'Escolha como o ATT deve se comportar ao abrir.',
                        'Configurações': 'Preferências, armazenamento local e informações de execução.'}
        self.subtitle.configure(text=descriptions.get(view, 'Gerencie versões, instale atualizações e acompanhe cada etapa.'))
        for frame in self.pages.values():frame.grid_remove()
        self.pages['Visão geral' if view in ('Visão geral','Atualizações') else view].grid()
        if view=='Atualizações':
            self.source_combo.grid();self.status_combo.grid()
        else:
            self.source_combo.grid_remove();self.status_combo.grid_remove()
        self._responsive(self.app.root.winfo_width(),self.app.root.winfo_height())
        self.update()

    def _responsive(self, width, height):
        compact = width < 1100
        self.stats.grid_remove(); self.compact_stats.grid_remove()
        if self.view == 'Visão geral':
            (self.compact_stats if compact else self.stats).grid()
        if compact:
            self.execution.grid_remove()
            self.compact_progress.place(relx=1,x=-18,y=17,anchor='ne')
            self.options.configure(height=130)
            self.app.update_button.place(relx=1,x=-18,y=84,anchor='ne')
            self.app.stop_button.place(x=280,y=40)
            self.stop_note.place(x=309,y=70)
        else:
            self.execution.grid(); self.compact_progress.place_forget()
            self.options.configure(height=114)
            self.app.update_button.place(relx=1,x=-22,y=39,anchor='ne')
            self.app.stop_button.place(x=350,y=40)
            self.stop_note.place(x=379,y=70)

    def _resize(self, event):
        if event.widget == self.app.root and hasattr(self, 'options'):
            self._responsive(event.width, event.height)

    def accepts(self, key, package):
        a = self.app
        if self.source_filter.get() != 'Todas as origens' and package.source != self.source_filter.get():
            return False
        status = a.statuses[key]
        from att_widgets import description
        categories={'Navegador web':'Navegadores','Editor de código':'Desenvolvimento',
                    'Compactador de arquivos':'Utilitários','Reprodutor multimídia':'Multimídia'}
        if self.type_filter.get()!='Todos os tipos' and categories.get(description(package.identifier),'Outros')!=self.type_filter.get():
            return False
        checks = {'Pendentes': a._eligible(key), 'Selecionados': key in a.selected,
                  'Atualizados': status in ('Atualizado', 'Reinício necessário'),
                  'Falhas': status == 'Falhou', 'Bloqueados': bool(package.blocked)}
        return checks.get(self.status_filter.get(), True)

    def ordered(self):
        a = self.app
        if self.order.get()=='Ordenar por':return list(a.packages.items())
        return sorted(a.packages.items(), key=lambda item: (
            a.statuses[item[0]] if self.order.get() == 'Status' else '', item[1].name.casefold()),
            reverse=self.order.get() == 'Nome Z–A')

    def update(self):
        a = self.app
        if not hasattr(self, 'values') or not hasattr(a, 'update_button'):
            return
        successful = sum(entry['status'] in ('Atualizado', 'Reinício necessário') for entry in a.activity.entries)
        last = a.activity.last_check
        self.values[0].configure(text='—' if a.installed is None else str(len(a.installed)))
        self.values[1].configure(text=str(sum(a._eligible(key) for key in a.packages)) if a.checked else '—')
        self.values[2].configure(text='—' if a.activity.warning else str(successful))
        self.values[3].configure(text=datetime.fromisoformat(last).strftime('%H:%M') if last else '—')
        self.compact_stats.configure(text='   |   '.join(f'{title}: {value.cget("text")}' for title, value in zip(
            ('Instalados', 'Disponíveis', 'Atualizados pelo ATT', 'Verificação'), self.values)))
        self.last_check_label.configure(text=datetime.fromisoformat(last).strftime('%d/%m/%Y às %H:%M') if last else 'Ainda não verificado')
        self.device_status.configure(text='Consultando…' if a.busy == 'query' else 'Atualizando…' if a.busy == 'update'
                                      else 'Falha na consulta' if a.query_failed else 'Verificação concluída' if a.checked else 'Aguardando verificação')
        self.available_badge.configure(text=str(sum(a._eligible(key) for key in a.packages)))
        if last:
            checked=datetime.fromisoformat(last)
            months=('janeiro','fevereiro','março','abril','maio','junho','julho','agosto','setembro','outubro','novembro','dezembro')
            note=f'Hoje, {checked.day} de {months[checked.month-1]}' if checked.date()==datetime.now().astimezone().date() else checked.strftime('%d/%m/%Y')
            self.check_note.configure(text=note)
        else:self.check_note.configure(text='Ainda não verificado')
        self.execution_state.configure(text='EM EXECUÇÃO' if a.busy == 'update' else 'VERIFICANDO' if a.busy else 'EM ESPERA')
        a.update_button.configure(text=f'Atualizar {len(a.selected)} selecionados' if a.selected else 'Atualizar selecionados')
        eligible={key for key in a.packages if a._eligible(key)}
        a.select_button.configure(text='Limpar seleção' if eligible and eligible<=a.selected else 'Selecionar todos')
        selected = [key for key in a.packages if key in a.selected]
        keys = a.run_keys if a.busy == 'update' else selected or (a.run_keys if a.completed else [])
        self.queue_count.configure(text=f'{len(keys)} programas selecionados' if keys else 'Nenhum programa selecionado')
        self.queue_list.configure(state='normal')
        self.queue_list.delete('1.0', 'end')
        for index,key in enumerate(keys):
            if key not in a.packages:continue
            self.queue_list.insert('end', ('●  ' if index==0 else '◆  ')+a.packages[key].name+'\n','name')
            state='Pronto para iniciar' if index==0 and not a.busy else 'Aguardando' if a.statuses[key]=='Pendente' else a.statuses[key]
            self.queue_list.insert('end',state+'\n\n','detail')
        self.queue_list.configure(state='disabled')
        self.percent.configure(text=f'{round(a.completed / a.total * 100) if a.total else 0}%')
        origins = ('Todas as origens', *sorted({p.source for p in a.packages.values() if p.source}))
        self.source_combo.configure(values=origins)
        self.render_apps()
        self.render_history()

    def render_apps(self):
        if not hasattr(self, 'apps_tree'):
            return
        self.apps_tree.delete(*self.apps_tree.get_children())
        query = self.apps_filter.get().casefold().strip()
        for package in sorted(self.app.installed or [], key=lambda p: p.name.casefold()):
            if not query or query in (package.name + ' ' + package.identifier).casefold():
                self.apps_tree.insert('', 'end', values=(package.name, package.identifier, package.installed, package.source or 'Não informada'))
        self.inventory_info.configure(text=self.app.inventory_error or (
            f'{len(self.app.installed)} aplicativo(s) detectado(s) na última consulta.' if self.app.installed is not None
            else 'Inventário ainda não consultado. Clique em Verificar atualizações.'))

    def render_history(self):
        current = tuple((e['time'], e['identifier'], e['status']) for e in self.app.activity.entries)
        if getattr(self, '_history_signature', None) == current:
            return
        self._history_signature = current
        self.history_tree.delete(*self.history_tree.get_children())
        for index in reversed(range(len(self.app.activity.entries))):
            e = self.app.activity.entries[index]
            self.history_tree.insert('', 'end', iid=str(index), values=(
                datetime.fromisoformat(e['time']).strftime('%d/%m/%Y %H:%M'), e['name'], e['available'], e['status']))

    def _history_selected(self, _event):
        selection = self.history_tree.selection()
        if not selection:
            return
        e = self.app.activity.entries[int(selection[0])]
        self.history_details.configure(state='normal')
        self.history_details.delete('1.0', 'end')
        self.history_details.insert('1.0', f"{e['name']} | {e['identifier']} | {e['source']}\n{e['installed']} → {e['available']}\n{e['status']}\n{e['details']}")
        self.history_details.configure(state='disabled')
