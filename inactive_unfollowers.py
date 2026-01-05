#!/usr/bin/env python3
"""
Mastodon-Inactive-Unfollowers
Findet inaktive Accounts, die dir nicht zurückfolgen
"""

import requests
import argparse
import sys
from datetime import datetime, timedelta
import csv
import time


class InactiveUnfollowersFinder:
    def __init__(self, instance, token):
        """
        instance: Deine Mastodon-Instanz (z.B. 'mastodon.social')
        token: Dein Access Token
        """
        self.instance = instance
        self.token = token
        self.base_url = f"https://{instance}/api/v1"
        self.headers = {"Authorization": f"Bearer {token}"}

    def get_account_id(self):
        """Hole eigene Account-ID"""
        try:
            response = requests.get(
                f"{self.base_url}/accounts/verify_credentials",
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            return data['id'], data['acct']
        except Exception as e:
            print(f"❌ Fehler beim Abrufen der Account-ID: {e}")
            sys.exit(1)

    def get_all_pages(self, url, params=None):
        """Hole alle Seiten einer paginierten API-Response"""
        results = []

        while url:
            try:
                response = requests.get(url, headers=self.headers, params=params, timeout=10)
                response.raise_for_status()
                results.extend(response.json())

                # Nächste Seite aus Link-Header
                link_header = response.headers.get('Link', '')
                url = None
                if 'rel="next"' in link_header:
                    for link in link_header.split(','):
                        if 'rel="next"' in link:
                            url = link[link.find('<') + 1:link.find('>')]
                            params = None  # URL enthält bereits Parameter
                            break

                time.sleep(0.5)  # Rate limiting

            except Exception as e:
                print(f"⚠️  Warnung: {e}")
                break

        return results

    def get_following(self, account_id):
        """Hole alle Accounts, denen du folgst"""
        print("📥 Lade Accounts, denen du folgst...")
        url = f"{self.base_url}/accounts/{account_id}/following"
        following = self.get_all_pages(url, params={'limit': 80})
        print(f"   ✅ {len(following)} Accounts geladen")
        return following

    def get_followers(self, account_id):
        """Hole alle Accounts, die dir folgen"""
        print("📥 Lade Accounts, die dir folgen...")
        url = f"{self.base_url}/accounts/{account_id}/followers"
        followers = self.get_all_pages(url, params={'limit': 80})
        print(f"   ✅ {len(followers)} Accounts geladen")
        return followers

    def get_account_statuses(self, account_id, limit=1):
        """Hole letzte Posts eines Accounts"""
        try:
            response = requests.get(
                f"{self.base_url}/accounts/{account_id}/statuses",
                headers=self.headers,
                params={'limit': limit, 'exclude_replies': False, 'exclude_reblogs': False},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return []

    def parse_date(self, date_string):
        """Parse ISO 8601 Datum"""
        try:
            # Entferne Millisekunden und Timezone für einfaches Parsing
            if '.' in date_string:
                date_string = date_string.split('.')[0] + 'Z'
            return datetime.strptime(date_string.replace('Z', '+00:00').split('+')[0], '%Y-%m-%dT%H:%M:%S')
        except:
            return None

    def find_inactive_unfollowers(self, inactive_months=36):
        """Hauptlogik: Finde inaktive Accounts, die nicht zurückfolgen"""

        # Eigene Account-ID holen
        account_id, username = self.get_account_id()
        print(f"\n👤 Dein Account: @{username}\n")

        # Following und Followers laden
        following = self.get_following(account_id)
        followers = self.get_followers(account_id)

        # Follower-IDs für schnellen Lookup
        follower_ids = {f['id'] for f in followers}

        # Finde Accounts, die nicht zurückfolgen
        print(f"\n🔍 Analysiere {len(following)} Accounts...\n")

        not_following_back = []
        inactive_unfollowers = []

        cutoff_date = datetime.now() - timedelta(days=inactive_months * 30)

        for i, account in enumerate(following, 1):
            if i % 20 == 0:
                print(f"   ⏳ {i}/{len(following)} analysiert...")

            # Prüfe ob zurückfolgt
            if account['id'] not in follower_ids:
                not_following_back.append(account)

                # Prüfe letzte Aktivität
                statuses = self.get_account_statuses(account['id'], limit=1)

                if statuses:
                    last_status_date = self.parse_date(statuses[0]['created_at'])

                    if last_status_date and last_status_date < cutoff_date:
                        inactive_unfollowers.append({
                            'account': account,
                            'last_post_date': last_status_date,
                            'last_status': statuses[0]
                        })
                else:
                    # Keine Posts gefunden = sehr inaktiv
                    inactive_unfollowers.append({
                        'account': account,
                        'last_post_date': None,
                        'last_status': None
                    })

                time.sleep(0.3)  # Rate limiting

        print(f"   ✅ Analyse abgeschlossen\n")

        return {
            'total_following': len(following),
            'total_followers': len(followers),
            'not_following_back': not_following_back,
            'inactive_unfollowers': inactive_unfollowers,
            'inactive_months': inactive_months
        }

    def print_results(self, results):
        """Gebe Ergebnisse formatiert aus"""
        inactive = results['inactive_unfollowers']

        if not inactive:
            print("✨ Keine inaktiven Accounts gefunden, die dir nicht folgen!\n")
            print(f"📊 Zusammenfassung:")
            print(f"   Du folgst: {results['total_following']} Accounts")
            print(
                f"   Folgen dir zurück: {results['total_followers']} ({results['total_followers'] / results['total_following'] * 100:.1f}%)")
            print(
                f"   Folgen dir nicht: {len(results['not_following_back'])} ({len(results['not_following_back']) / results['total_following'] * 100:.1f}%)")
            print(f"   └─ davon inaktiv >{results['inactive_months']} Monate: 0")
            return

        print("=" * 80)
        print(f"👻 Inaktive Accounts, die dir nicht zurückfolgen:\n")

        # Sortiere nach Datum (älteste zuerst)
        inactive_sorted = sorted(inactive, key=lambda x: x['last_post_date'] or datetime.min)

        for item in inactive_sorted:
            account = item['account']
            last_date = item['last_post_date']

            acct = account['acct']
            if '@' not in acct:
                acct = f"{acct}@{self.instance}"

            print(f"@{acct}")
            print(f"├─ Name: {account.get('display_name', 'N/A')}")

            if last_date:
                days_ago = (datetime.now() - last_date).days
                years = days_ago // 365
                months = (days_ago % 365) // 30

                time_str = []
                if years > 0:
                    time_str.append(f"{years} Jahr{'e' if years > 1 else ''}")
                if months > 0:
                    time_str.append(f"{months} Monat{'e' if months > 1 else ''}")

                print(f"├─ Letzter Post: {last_date.strftime('%Y-%m-%d')} (vor {', '.join(time_str)})")
            else:
                print(f"├─ Letzter Post: Unbekannt (Account hat keine Posts)")

            print(f"├─ Folgt dir: ❌ Nein")
            print(f"└─ Profil: {account['url']}")
            print()

        print("=" * 80)
        print(f"\n📊 Zusammenfassung:")
        print(f"   Du folgst: {results['total_following']} Accounts")
        print(
            f"   Folgen dir zurück: {results['total_followers']} ({results['total_followers'] / results['total_following'] * 100:.1f}%)")
        print(
            f"   Folgen dir nicht: {len(results['not_following_back'])} ({len(results['not_following_back']) / results['total_following'] * 100:.1f}%)")
        print(
            f"   └─ davon inaktiv >{results['inactive_months']} Monate: {len(inactive)} ({len(inactive) / results['total_following'] * 100:.1f}%)")
        print()

    def export_csv(self, results, filename):
        """Exportiere Ergebnisse als CSV"""
        inactive = results['inactive_unfollowers']

        if not inactive:
            print("ℹ️  Keine Daten zum Exportieren")
            return

        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Username', 'Display Name', 'Last Post Date', 'Days Inactive', 'Profile URL'])

            for item in inactive:
                account = item['account']
                last_date = item['last_post_date']

                acct = account['acct']
                if '@' not in acct:
                    acct = f"{acct}@{self.instance}"

                days_inactive = (datetime.now() - last_date).days if last_date else 'Unknown'

                writer.writerow([
                    acct,
                    account.get('display_name', ''),
                    last_date.strftime('%Y-%m-%d') if last_date else 'Unknown',
                    days_inactive,
                    account['url']
                ])

        print(f"💾 Exportiert nach: {filename}\n")

    def unfollow_accounts(self, results):
        """Entfolge den gefundenen Accounts (mit Bestätigung)"""
        inactive = results['inactive_unfollowers']

        if not inactive:
            print("ℹ️  Keine Accounts zum Entfolgen")
            return

        print(f"\n⚠️  Du bist dabei, {len(inactive)} Accounts zu entfolgen!")
        print("Möchtest du fortfahren? (ja/nein): ", end='')

        response = input().strip().lower()

        if response not in ['ja', 'j', 'yes', 'y']:
            print("❌ Abgebrochen")
            return

        print("\n🔄 Entfolge Accounts...\n")

        success_count = 0
        for item in inactive:
            account = item['account']
            acct = account['acct']
            if '@' not in acct:
                acct = f"{acct}@{self.instance}"

            try:
                response = requests.post(
                    f"{self.base_url}/accounts/{account['id']}/unfollow",
                    headers=self.headers,
                    timeout=10
                )
                response.raise_for_status()
                print(f"   ✅ @{acct}")
                success_count += 1
                time.sleep(0.5)  # Rate limiting
            except Exception as e:
                print(f"   ❌ @{acct}: {e}")

        print(f"\n✨ {success_count}/{len(inactive)} Accounts entfolgt\n")


def main():
    parser = argparse.ArgumentParser(
        description='Mastodon-Inactive-Unfollowers: Finde inaktive Accounts, die dir nicht folgen',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  %(prog)s --instance mastodon.social --token YOUR_TOKEN
  %(prog)s -i chaos.social -t YOUR_TOKEN --inactive-months 24
  %(prog)s -i mastodon.social -t YOUR_TOKEN --export inactive.csv
  %(prog)s -i mastodon.social -t YOUR_TOKEN --unfollow

Access Token erstellen:
  1. Gehe zu: https://DEINE-INSTANZ/settings/applications
  2. Erstelle neue Anwendung
  3. Benötigte Scopes: read:accounts, read:follows, write:follows (für --unfollow)
  4. Kopiere den Access Token
        """
    )

    parser.add_argument('-i', '--instance', required=True,
                        help='Deine Mastodon-Instanz (z.B. mastodon.social)')
    parser.add_argument('-t', '--token', required=True,
                        help='Dein Access Token')
    parser.add_argument('--inactive-months', type=int, default=36,
                        help='Inaktivitätszeitraum in Monaten (Standard: 36)')
    parser.add_argument('--export',
                        help='Exportiere Ergebnisse als CSV')
    parser.add_argument('--unfollow', action='store_true',
                        help='Entfolge gefundenen Accounts (nach Bestätigung)')

    args = parser.parse_args()

    # Validierung
    if args.inactive_months < 1:
        print("❌ Fehler: inactive-months muss mindestens 1 sein")
        sys.exit(1)

    # Banner
    print("\n" + "=" * 80)
    print("👻 Mastodon-Inactive-Unfollowers")
    print("   Finde inaktive Accounts, die dir nicht zurückfolgen")
    print("=" * 80 + "\n")

    # Finder erstellen und ausführen
    finder = InactiveUnfollowersFinder(args.instance, args.token)
    results = finder.find_inactive_unfollowers(args.inactive_months)
    finder.print_results(results)

    if args.export:
        finder.export_csv(results, args.export)

    if args.unfollow:
        finder.unfollow_accounts(results)


if __name__ == "__main__":
    main()