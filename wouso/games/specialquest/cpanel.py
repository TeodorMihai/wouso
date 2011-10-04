# views for wouso cpanel
from django.contrib.auth.decorators import permission_required
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template import RequestContext
from wouso.core.user.models import Player
from wouso.core import scoring
from wouso.core.qpool import get_questions_with_category
from models import SpecialQuestTask, SpecialQuestUser, SpecialQuestGame
from forms import TaskForm

@permission_required('specialquest.change_specialquest')
def home(request):
    tasks = SpecialQuestTask.objects.all()

    return render_to_response('specialquest/cpanel_home.html',
                              {'tasks': tasks,
                               'module': 'specialquest'},
                              context_instance=RequestContext(request))

@permission_required('specialquest.change_specialquest')
def edit(request, id=None):
    if id is not None:
        task = get_object_or_404(SpecialQuestTask, pk=id)
    else:
        task = None

    form = TaskForm(instance=task)

    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('wouso.games.specialquest.cpanel.home'))

    return render_to_response('specialquest/cpanel_edit.html',
                              {'task': task,
                               'form': form,
                               'module': 'specialquest'},
                              context_instance=RequestContext(request))

@permission_required('specialquest.change_specialquest')
def delete(request, id=None):
    if id is None:
        return HttpResponseRedirect(reverse('wouso.games.specialquest.cpanel.home'))
    task = get_object_or_404(SpecialQuestTask, pk=id)
    task.delete()
    return HttpResponseRedirect(reverse('wouso.games.specialquest.cpanel.home'))

@permission_required('specialquest.change_specialquest')
def manage_player(request, player_id):
    player = get_object_or_404(Player, pk=player_id)
    player = player.get_extension(SpecialQuestUser)
    tasks_not_done = SpecialQuestTask.objects.exclude(id__in=player.done_tasks.all().values('id')).all()

    # TODO: use smth like django-flash for this
    message, error = '', ''

    if request.method == "POST":
        # do bonuses
        try:
            amount = int(request.POST.get('gold', 0))
        except ValueError:
            amount = 0
        if amount > 0:
            scoring.score(player, None, 'bonus-gold', external_id=request.user.get_profile().id, gold=amount)
            message = 'Successfully given bonus'
        else:
            error = 'Invalid amount'

    bonuses = scoring.History.objects.filter(user=player, formula__id='bonus-gold')

    return render_to_response('specialquest/cpanel_manage.html',
                    dict(player=player, tasks_not_done=tasks_not_done, message=message, error=error, bonuses=bonuses),
                    context_instance=RequestContext(request))

@permission_required('specialquest.change_specialquest')
def manage_player_set(request, player_id, task_id):
    player = get_object_or_404(SpecialQuestUser, id=player_id)
    task = get_object_or_404(SpecialQuestTask, id=task_id)

    if task not in player.done_tasks.all():
        player.done_tasks.add(task)
        scoring.score(player, SpecialQuestGame, 'specialquest-passed',external_id=task.id, value=task.value)

    return HttpResponseRedirect(reverse('specialquest_manage', args=(player.id,)))

@permission_required('specialquest.change_specialquest')
def manage_player_unset(request, player_id, task_id):
    player = get_object_or_404(SpecialQuestUser, id=player_id)
    task = get_object_or_404(SpecialQuestTask, id=task_id)

    if task in player.done_tasks.all():
        player.done_tasks.remove(task)
        scoring.unset(player, SpecialQuestGame, 'specialquest-passed', external_id=task.id)

    return HttpResponseRedirect(reverse('specialquest_manage', args=(player.id,)))