import pytest

from scripts.backlog import STATUS, ler, lista

OBRIGATORIOS = ("status", "papel", "depende", "ambiente", "toca", "pronto", "prompt")
AMBIENTES = ("offline", "fabric", "humano")


@pytest.fixture(scope="module")
def tarefas():
    return ler()[1]


def test_toda_tarefa_tem_campos_obrigatorios(tarefas):
    faltando = {t["id"]: [c for c in OBRIGATORIOS if not t.get(c)] for t in tarefas.values()}
    assert {k: v for k, v in faltando.items() if v} == {}


def test_status_e_ambiente_validos(tarefas):
    assert all(t["status"] in STATUS for t in tarefas.values())
    assert all(t["ambiente"] in AMBIENTES for t in tarefas.values())


def test_dependencias_existem_e_nao_ha_ciclo(tarefas):
    for t in tarefas.values():
        assert all(d in tarefas for d in lista(t["depende"])), t["id"]

    visitando, ok = set(), set()

    def visita(tid):
        assert tid not in visitando, f"ciclo em {tid}"
        if tid in ok:
            return
        visitando.add(tid)
        for d in lista(tarefas[tid]["depende"]):
            visita(d)
        visitando.discard(tid)
        ok.add(tid)

    for tid in tarefas:
        visita(tid)


def test_toca_sem_espaco_dentro_do_caminho(tarefas):
    assert all(" " not in c for t in tarefas.values() for c in lista(t["toca"]))


def test_tarefas_que_publicam_exigem_confirmacao_explicita(tarefas):
    # T31 e T35 publicam em produção: o prompt deve mandar pedir confirmação explícita.
    for tid in ("T31", "T35"):
        assert "confirmação explícita" in tarefas[tid]["prompt"]
