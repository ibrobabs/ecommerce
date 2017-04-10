from django.shortcuts import render
from payments.models import User
from main.models import MarketingItem, StatusReport, Announcement
from datetime import date, timedelta


class market_item(object):

	def __init__(self, img, heading, caption, button_link="register", button_title="View details"):

		self.img = img
		self.heading = heading
		self.caption = caption
		self.button_link = button_link
		self.button_title = button_title


market_items = [
	market_item(
		img="yoda.jpg",
		heading="Hone your Jedi Skills",
		caption="All members have access to our unique"
		" training and achievements latters. Progress through the "
		"levels and show everyone who the top Jedi Master is!",
		button_title="Sign Up Now"
	),
	market_item(
		img="clone_army.jpg",
		heading="Build your Clan",
		caption="Engage in meaningful conversation, or "
		"blooodthirsty battle! If it's related to "
		"Star Wars, in any way, you better believe we do it.",
		button_title="Sign Up Now"
	),
	market_item(
		img="leia.jpg",
		heading="Find Love",
		caption="Everybody knows Star Wars fans are the "
		"best mates for Star Wars fans. Find your "
		"stars together.",
		button_title="Sign Up Now"
	),
]

def index(request):
	uid = request.session.get('user')
	if uid is None:
		market_items = MarketingItem.objects.all()
		return render(request, 'main/index.html', {'marketing_items': market_items})
	else:
		status = StatusReport.objects.all().order_by('-when')[:20]

		announce_date = date.today() - timedelta(days=30)
		announce = (Announcement.objects.filter(when__gt=announce_date).order_by('-when'))

		usr = User.get_by_id(uid)
		badges = usr.badges.all()

		return render(
			request,
			'main/user.html',
			{'user': usr, 'badges': badges, 'reports': status, 'announce': announce},
		)

def report(request):
	if request.method == "POST":
		status = request.POST.get("status", "")

		if status:
			uid = request.session.get('user')
			user = User.get_by_id(uid)
			StatusReport(user=user, status=status).save()

		return index(request)